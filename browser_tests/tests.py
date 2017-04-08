from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from urllib.parse import urljoin
from selenium import webdriver


class BrowserStackTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(BrowserStackTestCase, cls).setUpClass()
        desired_cap = {
            'browser': 'Chrome',
            'browser_version': '57.0',
            'os': 'Windows',
            'os_version': '7',
            'resolution': '1024x768',
        }
        USERNAME = settings.BROWSER_STACK_ID
        ACCESS_KEY = settings.BROWSER_STACK_KEY

        cls.desired_capabilities = desired_cap
        cls.desired_capabilities['browserstack.local'] = True
        cls.desired_capabilities['browserstack.debug'] = True
        url = 'http://%s:%s@hub.browserstack.com:80/wd/hub'
        cls.selenium = webdriver.Remote(
            desired_capabilities=cls.desired_capabilities,
            command_executor=url % (USERNAME, ACCESS_KEY)
        )
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(BrowserStackTestCase, cls).tearDownClass()


class ExampleTests(BrowserStackTestCase):

    def test_homepage(self):
        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_id(
            'apply-now').click()
        self.assertEquals(urljoin(self.live_server_url, 'apply/'),
                          self.selenium.current_url)
        submit = self.selenium.find_element_by_css_selector(
            'button[type="submit"]')
        self.assertEquals(submit.text, 'Apply')
