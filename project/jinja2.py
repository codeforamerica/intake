from datetime import datetime
from urllib.parse import urljoin
from pytz import timezone
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import mark_safe
from django.conf import settings
from django.contrib.humanize.templatetags import humanize
from django.contrib.staticfiles.storage import staticfiles_storage
from rest_framework.renderers import JSONRenderer
from jinja2 import Environment, Markup
from markupsafe import escape
import phonenumbers
from project.services.query_params import get_url_for_ids

url_with_ids = get_url_for_ids


def loudfail_static(*args, **kwargs):
    result = staticfiles_storage.url(*args, **kwargs)
    if not result:
        raise ObjectDoesNotExist(
            "Cannot find static file with: {} {}".format(args, kwargs))
    else:
        return result


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': loudfail_static,
        'url': reverse,
        "content": "project.content.constants",
        "linkify": "project.jinja2.linkify",
        "current_local_time": "project.jinja2.current_local_time",
        "namify": "project.jinja2.namify",
        "url_with_ids": "project.jinja2.url_with_ids",
        "oxford_comma": "project.jinja2.oxford_comma",
        "contact_info_to_html": "project.jinja2.contact_info_to_html",
        "to_json": "project.jinja2.to_json",
        "humanize": "project.jinja2.humanize",
        "contact_method_verbs": "project.jinja2.contact_method_verbs",
        "format_phone_number": "project.jinja2.format_phone_number",
        "settings": "django.conf.settings",
        "local_time": "intake.utils.local_time",
    })
    return env


def externalize_url(url):
    return urljoin(settings.DEFAULT_HOST, url)


def external_reverse(view_name):
    return externalize_url(reverse(view_name))


def to_json(data):
    return mark_safe(JSONRenderer().render(data).decode('utf-8'))


def namify(s=''):
    words = s.split()
    if not words:
        return s
    first = words[0]
    # only capitalize if they use all caps or all lowercase
    if first == first.lower() or first == first.upper():
        first = first.capitalize()
    return ' '.join([first] + words[1:])


def oxford_comma(things, use_or=False):
    things = list(things)
    sep = "or" if use_or else "and"
    if not things:
        return ""
    if len(things) == 1:
        return str(things[0])
    elif len(things) == 2:
        return (" " + sep + " ").join(map(str, things))
    return ", ".join(
        list(map(str, things[:-1])) + [sep + " " + str(things[-1])])


def format_phone_number(phone_number_string):
    parsed = phonenumbers.parse(phone_number_string, 'US')
    return phonenumbers.format_number(
        parsed, phonenumbers.PhoneNumberFormat.NATIONAL)


contact_medium_verb_lookup = dict(
    email='emailed',
    sms='texted'
)


def contact_method_verbs(mediums):
    return oxford_comma([
        contact_medium_verb_lookup[medium]
        for medium in mediums
    ])


def contact_info_to_html(contact_info_dict):
    phone = contact_info_dict.get('sms', '')
    if phone:
        phone = format_phone_number(phone)
    email = contact_info_dict.get('email', '')

    html = oxford_comma([
        thing for thing in (phone, email) if thing])
    return mark_safe(html)


class Linkifier:

    def __init__(self, links):
        self.links = links

    def build_link(self, lookup):
        url = self.links[lookup]
        return '<a href="{}">{}</a>'.format(
            url, escape(lookup))

    def __call__(self, content):
        output = content
        for str_lookup in self.links:
            if str_lookup in output:
                link = self.build_link(str_lookup)
                output = output.replace(str_lookup, link)
        return Markup(output)


def current_local_time(fmt):
    utc_now = timezone('GMT').localize(datetime.utcnow())
    return utc_now.astimezone(timezone('US/Pacific')).strftime(fmt)


linkify_links = {
    "Code for America": "https://codeforamerica.org",
    "Privacy Policy": reverse_lazy("intake-privacy"),
    "San Francisco Public Defender": "/partners/sf_pubdef/",
    "Contra Costa Public Defender": "/partners/cc_pubdef/",
    "Alameda County Public Defender's Office": "/partners/a_pubdef/",
    "East Bay Community Law Center": "/partners/ebclc/",
    "Monterey County Public Defender": "/partners/monterey_pubdef/",
    "Solano County Public Defender": "/partners/solano_pubdef/",
    "San Diego County Public Defender": "/partners/san_diego_pubdef/",
    "San Joaquin County Public Defender": "/partners/san_joaquin_pubdef/",
    "Santa Clara County Public Defender": "/partners/santa_clara_pubdef/",
    "Santa Cruz County Public Defender": "/partners/santa_cruz_pubdef/",
    "Fresno County Public Defender": "/partners/fresno_pubdef/",
    "Sonoma County Public Defender": "/partners/sonoma_pubdef/",
    "Tulare County Public Defender": "/partners/tulare_pubdef/",
    "Santa Barbara County Public Defender": "/partners/santa_barbara_pubdef/",
    "Ventura County Public Defender": "/partners/ventura_pubdef/",
    "Yolo County Public Defender": "/partners/yolo_pubdef/",
    "Stanislaus County Public Defender": "/partners/stanislaus_pubdef/",
    "Marin County Public Defender": "/partners/marin_pubdef/",
    "clearmyrecord@codeforamerica.org":
        "mailto:clearmyrecord@codeforamerica.org",
    "(415) 301-6005": "tel:14153016005"
}

linkify = Linkifier(linkify_links)
