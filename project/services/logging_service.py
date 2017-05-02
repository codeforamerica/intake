import logging
from django.utils import timezone

"""
Tab separated? Space separated?
key=value key2="value2"
page_name="/url/"
https://docs.djangoproject.com/en/1.11/topics/logging/#making-logging-calls

Goals:
- everything that goes to mixpanel is logged to stdout
- we can add lots of properties on the fly easily to both mixpanel & std out
- easy to add new calls in the codebase

"""

logger = logging.getLogger(__name__)

timestamp_format = '%Y-%m-%d %H:%M:%S.%f'


def format_and_log(log_type, level='INFO', **data):

    """log string in format: <log_datetime> <level> <log_type>
    <unpacked kwargs in key=value format separated by tabs>
    """
    formatted_key_values = [
        "{}={}".format(key, value) for key, value in data.items()]
    formatted_log = "\t".join([
        timezone.now().strftime(timestamp_format),
        level,
        log_type,
        *formatted_key_values
    ])
    print(formatted_log)
    # figure out where to send/save this
