from browserstack.local import Local
from django.conf import settings
from urllib.parse import urljoin
from selenium import webdriver
from project.fixtures_index import ESSENTIAL_DATA_FIXTURES

USERNAME = settings.BROWSER_STACK_ID
ACCESS_KEY = settings.BROWSER_STACK_KEY


def start_local():
    """Code to start browserstack local before start of test."""
    global bs_local
    bs_local = Local()
    bs_local_args = {"key": ACCESS_KEY, "forcelocal": "true"}
    bs_local.start(**bs_local_args)


def stop_local():
    """Code to stop browserstack local after end of test."""
    global bs_local
    if bs_local is not None:
        bs_local.stop()


def before_all(context):
    start_local()
    desired_cap = {
        'browser': 'Chrome',
        'browser_version': '57.0',
        'os': 'Windows',
        'os_version': '7',
        'resolution': '1024x768',
    }
    desired_capabilities = desired_cap
    desired_capabilities['browserstack.local'] = True
    desired_capabilities['browserstack.debug'] = True
    url = 'http://%s:%s@hub.browserstack.com:80/wd/hub'
    context.browser = webdriver.Remote(
        desired_capabilities=desired_capabilities,
        command_executor=url % (USERNAME, ACCESS_KEY)
    )
    context.browser.implicitly_wait(10)


def after_all(context):
    context.browser.quit()
    stop_local()


def before_scenario(context, scenario):
    context.fixtures = ['counties', 'organizations']
