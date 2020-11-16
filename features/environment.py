from django.conf import settings
from django.core.management import call_command
from selenium import webdriver


# -- FILE: features/environment.py
# USE: behave -D BEHAVE_DEBUG_ON_ERROR         (to enable  debug-on-error)
# USE: behave -D BEHAVE_DEBUG_ON_ERROR=yes     (to enable  debug-on-error)
# USE: behave -D BEHAVE_DEBUG_ON_ERROR=no      (to disable debug-on-error)

BEHAVE_DEBUG_ON_ERROR = False


def setup_debug_on_error(userdata):
    global BEHAVE_DEBUG_ON_ERROR
    BEHAVE_DEBUG_ON_ERROR = userdata.getbool("BEHAVE_DEBUG_ON_ERROR")


def before_all(context):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    # fixes weird chrome keychain popup, as described here:
    # https://groups.google.com/d/msg/chromedriver-users/ktp-s_0M5NM/lFerFJSlAgAJ
    options.add_argument("enable-features=NetworkService,NetworkServiceInProcess")

    context.browser = webdriver.Chrome(chrome_options=options)
    context.browser.implicitly_wait(10)
    settings.DIVERT_REMOTE_CONNECTIONS = True
    setup_debug_on_error(context.config.userdata)


def django_ready(context):
    context.test.patches = {}


def after_all(context):
    context.browser.quit()


def before_scenario(context, scenario):
    call_command('load_essential_data')


def after_scenario(context, scenario):
    for patch_name, patch in context.test.patches.items():
        patch.stop()


def after_step(context, step):
    # from https://github.com/behave/behave/blob/master/docs/tutorial.rst#
    #       debug-on-error-in-case-of-step-failures
    # and https://stackoverflow.com/a/22344473/399726
    if BEHAVE_DEBUG_ON_ERROR and step.status == "failed":
        # -- ENTER DEBUGGER: Zoom in on failure location.
        # NOTE: Use IPython debugger, same for pdb (basic python debugger).
        import ipdb
        ipdb.post_mortem(step.exc_traceback)
