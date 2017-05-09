import random
from django.db import models
from django.http.request import QueryDict
from django.utils import timezone
from pytz import timezone as pytz_timezone
from intake.constants import (
    PACIFIC_TIME, STAFF_NAME_CHOICES, DEFAULT_ORGANIZATION_ORDER
)
from django.template import loader

jinja = None


def load_jinja():
    return loader.engines['jinja']


def local_time(dt, fmt=None, tz_name='US/Pacific'):
    local_datetime = dt.astimezone(pytz_timezone(tz_name))
    if not fmt:
        return local_datetime
    return local_datetime.strftime(fmt)


def get_todays_date():
    return timezone.now().astimezone(PACIFIC_TIME).date()


def get_random_staff_name():
    return random.choice(STAFF_NAME_CHOICES)


def sort_orgs_in_default_order(orgs):
    if not orgs:
        return orgs
    if hasattr(orgs[0], 'slug'):
        return sorted(
            orgs, key=lambda org: DEFAULT_ORGANIZATION_ORDER.index(org.slug))
    else:
        return sorted(
            orgs,
            key=lambda org: DEFAULT_ORGANIZATION_ORDER.index(org['slug']))


def save_form_data_to_session(request, session_key, query_dict):
    # this should update data, not simply overwrite it.
    data_dict = {
        key: items
        for key, items in query_dict._iterlists()
    }
    existing_data = request.session.get(session_key, {})
    existing_data.update(data_dict)
    request.session[session_key] = existing_data


def get_form_data_from_session(request, session_key):
    """Gets a dictionary from the session based on a key
        and converts each key, list pair into a mutable QueryDict
        so that it can be processed by a form as if it were post data
    """
    raw_dict = request.session.get(session_key, {})
    qdict = QueryDict('', mutable=True)
    for key, items in raw_dict.items():
        if not isinstance(items, list):
            items = [items]
        qdict.setlist(key, items)
    return qdict


def clear_session_data(request, *keys):
    existing_keys = list(request.session.keys())
    for key_to_delete in keys:
        if key_to_delete in existing_keys:
            del request.session[key_to_delete]


def clear_form_data_from_session(request, session_key):
    request.session[session_key] = {}


def coerce_to_ids(items):
    for item in items:
        if isinstance(item, models.Model):
            yield item.id
        else:
            yield item


def is_the_weekend():
    """datetime.weekday() returns 0 for Monday, 6 for Sunday
    """
    return timezone.now().weekday() in [5, 6]


def get_page_navigation_counter(page, wing_size=3, gap_symbol='jump'):
    """Takes a Page object (see django.core.paginator)
        returns a list of page numbers suitable for a pagination nav
        wing_size is at least 3
    """
    wing_size = max(wing_size, 3)
    total = page.paginator.num_pages
    full_range = list(page.paginator.page_range)
    page_index = full_range.index(page.number)
    wing_span = (wing_size * 2) + 1
    shoulder_span = wing_span - 2
    if total <= wing_span:
        return full_range
    left_side = set(full_range[:shoulder_span])
    left_gap = [full_range[0], gap_symbol]
    right_gap = [gap_symbol, full_range[-1]]
    right_side = set(full_range[-shoulder_span:])
    shoulder_size = wing_size - 2
    left_index = max((
        page_index - shoulder_size, 0))
    right_index = min((
        page_index + shoulder_size + 1, total - 1))
    window = set(full_range[left_index:right_index])
    if window <= left_side:
        return sorted(list(left_side)) + right_gap
    elif window <= right_side:
        return left_gap + sorted(list(right_side))
    else:
        return left_gap + sorted(list(window)) + right_gap


def compile_template_string(template_string):
    global jinja
    if not jinja:
        jinja = load_jinja()
    return jinja.env.from_string(template_string)


def render_template_string(template_string, context):
    return compile_template_string(template_string).render(context)
