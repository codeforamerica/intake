import sys
import cProfile
from pstats import Stats
import os
import time
from django.core import mail
from django.conf import settings
from django.test import override_settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


# device sizes
SMALL_MOBILE = {'width': 320, 'height': 570}
COMMON_MOBILE = {'width': 360, 'height': 640}
BIG_MOBILE = {'width': 720, 'height': 1280}
SMALL_DESKTOP = {'width': 1280, 'height': 800}
LARGE_DESKTOP = {'width': 1440, 'height': 900}


class ElementDoesNotExistError(Exception):
    pass


# needs the basic static file storage to properly serve files
@override_settings(
    STATICFILES_STORAGE=str(
        'django.contrib.staticfiles.storage.StaticFilesStorage'),
    INSIDE_A_TEST=True)
class FunctionalTestCase(StaticLiveServerTestCase):
    device = None
    dimensions = COMMON_MOBILE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.DEBUG:
            settings.DEBUG = True

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        from selenium import webdriver
        cls.driver = webdriver
        cls.browser = webdriver.Firefox()
        cls.browser.set_window_size(
            cls.dimensions['width'],
            cls.dimensions['height'])

    def build_url(self, url):
        return self.host + url

    def get(self, url, host=None):
        full_url = self.build_url(url)
        self.browser.get(full_url)

    def set_size(self, size_config):
        self.browser.set_window_size(
            size_config['width'],
            size_config['height'])

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.host = os.environ.get(
            'ACCEPTANCE_TEST_HOST',
            self.live_server_url)
        self.browser.delete_all_cookies()

    def click_on(self, text):
        self.browser.find_element_by_link_text(text).click()

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        cls.browser.close()
        super().tearDownClass(*args, **kwargs)

    def screenshot(self, filename):
        path = os.path.join('tests/screenshots', filename)
        self.browser.save_screenshot(path)

    def handle_checkbox_input(self, inputs, value):
        if not isinstance(value, str) and hasattr(value, "__iter__"):
            # there are multiple values
            def should_click(x):
                return x in value
        else:
            def should_click(x):
                return x == value
        for element in inputs:
            if should_click(element.get_attribute('value')):
                element.click()

    def handle_input(self, name, value):
        elements = self.browser.find_elements_by_name(name)
        if not elements:
            raise ElementDoesNotExistError(
                "could not find element with name '{}'".format(name))
        input_type = elements[0].get_attribute('type')
        if input_type == 'checkbox':
            self.handle_checkbox_input(elements, value)
        elif input_type in ['radio', 'submit']:
            for element in elements:
                if element.get_attribute('value') == value:
                    element.click()
            if input_type == 'submit':
                return True
        elif elements[0].tag_name == 'select':
            select = self.driver.support.ui.Select(elements[0])
            select.select_by_value(value)
        else:
            elements[0].clear()
            elements[0].send_keys(value)

    def fill_form(self, **answers):
        for name, value in answers.items():
            hit_submit = self.handle_input(name, value)
        if not hit_submit:
            form = self.browser.find_element_by_tag_name('form')
            form.submit()

    def wait(self, seconds):
        time.sleep(seconds)

# relevant:
# nopep8 http://selenium-python.readthedocs.io/faq.html#how-to-scroll-down-to-the-bottom-of-a-page


class ScreenSequenceTestCase(FunctionalTestCase):

    def handle_callable_args(self, args_list, kwargs_dict):
        new_args = []
        for arg in args_list:
            if hasattr(arg, '__call__'):
                new_args.append(arg())
            else:
                new_args.append(arg)
        new_kwargs = {}
        for key, value in kwargs_dict.items():
            if hasattr(value, '__call__'):
                new_kwargs[key] = value()
            else:
                new_kwargs[key] = value
        return new_args, new_kwargs

    def build_filepath(self, prefix, i, method, ext='.png'):
        if not prefix:
            prefix = getattr(self, 'sequence_prefix', self.__class__.__name__)
        filename = '{prefix}-{index:03d}__{method}{ext}'.format(
            prefix=prefix, index=i, method=method, ext=ext)
        return filename

    def print_email(self, filepath):
        filepath = os.path.join('tests/screenshots', filepath)
        email = mail.outbox[-1]
        contents = '\n'.join([
            "EMAIL to " + ', '.join(email.to),
            "\n----------------------------\n",
            email.subject,
            "\n----------------------------\n",
            email.body
        ])
        with open(filepath, 'w') as outfile:
            outfile.write(contents)

    def run_sequence(self, prefix, sequence,
                     size=COMMON_MOBILE, full_height=True):
        self.set_size(size)
        for i, step in enumerate(sequence):
            step_name, att_name, args, kwargs = step
            if att_name == 'print_email':
                self.print_email(
                    self.build_filepath(
                        prefix, i, step_name, ext='.txt'))
                continue
            method = getattr(self, att_name)
            args, kwargs = self.handle_callable_args(args, kwargs)
            method(*args, **kwargs)
            if full_height:
                body = self.browser.find_element_by_tag_name('body')
                height = max(
                    size['height'], int(
                        body.get_attribute('scrollHeight')))
                self.set_size(dict(width=size['width'], height=height))
            self.screenshot(self.build_filepath(prefix, i, step_name))


def respond_with(response):
    def wrapped(*args, **kwargs):
        return response('Test exception')
    return wrapped


class TimeProfileTestMixin:
    """A mixin that allows code to be profiled using cProfile
    """
    @classmethod
    def setUpClass(cls):
        search_term = '--profile'
        for arg in sys.argv:
            if search_term in arg:
                cls.should_profile = True

    def setUp(self):
        super().setUp()
        if self.should_profile:
            self.profile = cProfile.Profile()
            self.profile.enable()

    def tearDown(self):
        if self.should_profile:
            results = Stats(self.profile)
            results.strip_dirs()
            results.sort_stats('cumulative')
            results.print_stats(50)
        super().tearDown()


# TODO: maybe this should be a config file not python
class DEVICES:
    Apple_iPhone_3GS = "Apple iPhone 3GS"
    Apple_iPhone_4 = "Apple iPhone 4"
    Apple_iPhone_5 = "Apple iPhone 5"
    Apple_iPhone_6 = "Apple iPhone 6"
    Apple_iPhone_6_Plus = "Apple iPhone 6 Plus"
    BlackBerry_Z10 = "BlackBerry Z10"
    BlackBerry_Z30 = "BlackBerry Z30"
    Google_Nexus_4 = "Google Nexus 4"
    Google_Nexus_5 = "Google Nexus 5"
    Google_Nexus_S = "Google Nexus S"
    HTC_Evo_Touch_HD_Desire_HD_Desire = "HTC Evo, Touch HD, Desire HD, Desire"
    HTC_One_X_EVO_LTE = "HTC One X, EVO LTE"
    HTC_Sensation_Evo_3D = "HTC Sensation, Evo 3D"
    LG_Optimus_2X_Optimus_3D_Optimus_Black = \
        "LG Optimus 2X, Optimus 3D, Optimus Black"
    LG_Optimus_G = "LG Optimus G"
    LG_Optimus_LTE_Optimus_4X_HD = "LG Optimus LTE, Optimus 4X HD"
    LG_Optimus_One = "LG Optimus One"
    Motorola_Defy_Droid_Droid_X_Milestone = ("Motorola Defy, Droid, Droid X, "
                                             "Milestone")
    Motorola_Droid_3_Droid_4_Droid_Razr_Atrix_4G_Atrix_2 = (
        "Motorola Droid 3,"
        " Droid 4, Droid Razr, Atrix 4G, Atrix 2"
    )
    Motorola_Droid_Razr_HD = "Motorola Droid Razr HD"
    Nokia_C5_C6_C7_N97_N8_X7 = "Nokia C5, C6, C7, N97, N8, X7"
    Nokia_Lumia_7X0_Lumia_8XX_Lumia_900_N800_N810_N900 = (
        "Nokia Lumia 7X0, "
        "Lumia 8XX, Lumia 900, N800, N810, N900"
    )
    Samsung_Galaxy_Note_3 = "Samsung Galaxy Note 3"
    Samsung_Galaxy_Note_II = "Samsung Galaxy Note II"
    Samsung_Galaxy_Note = "Samsung Galaxy Note"
    Samsung_Galaxy_S_III_Galaxy_Nexus = "Samsung Galaxy S III, Galaxy Nexus"
    Samsung_Galaxy_S_S_II_W = "Samsung Galaxy S, S II, W"
    Samsung_Galaxy_S4 = "Samsung Galaxy S4"
    Sony_Xperia_S_Ion = "Sony Xperia S, Ion"
    Sony_Xperia_Sola_U = "Sony Xperia Sola, U"
    Sony_Xperia_Z_Z1 = "Sony Xperia Z, Z1"
    Amazon_Kindle_Fire_HDX7 = "Amazon Kindle Fire HDX 7″"
    Amazon_Kindle_Fire_HDX8_9 = "Amazon Kindle Fire HDX 8.9″"
    Amazon_Kindle_Fire_First_Generation = \
        "Amazon Kindle Fire (First Generation)"
    Apple_iPad_1_2_iPad_Mini = "Apple iPad 1 / 2 / iPad Mini"
    Apple_iPad_3_4 = "Apple iPad 3 / 4"
    BlackBerry_PlayBook = "BlackBerry PlayBook"
    Google_Nexus_10 = "Google Nexus 10"
    Google_Nexus_7_2 = "Google Nexus 7 2"
    Google_Nexus_7 = "Google Nexus 7"
    Motorola_Xoom_Xyboard = "Motorola Xoom, Xyboard"
    Samsung_Galaxy_Tab_7_7_8_9_10_1 = "Samsung Galaxy Tab 7.7, 8.9, 10.1"
    Samsung_Galaxy_Tab = "Samsung Galaxy Tab"
    Notebook_with_touch = "Notebook with touch"
