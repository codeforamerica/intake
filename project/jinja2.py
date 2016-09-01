from django.contrib.humanize.templatetags import humanize
from django.core.urlresolvers import reverse, reverse_lazy

from jinja2 import Environment
from datetime import datetime
from pytz import timezone
from jinja2 import Markup


def namify(s=''):
    words = s.split()
    if not words:
        return s
    first = words[0]
    # only capitalize if they use all caps or all lowercase
    if first == first.lower() or first == first.upper():
        first = first.capitalize()
    return ' '.join([first] + words[1:])


def url_with_ids(view_name, ids):
    url = reverse(view_name)
    params = '?ids=' + ','.join([str(i) for i in ids])
    return url + params


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


class Linkifier:

    def __init__(self, links):
        self.links = links

    def build_link(self, lookup):
        url = self.links[lookup]
        return '<a href="{}">{}</a>'.format(
            url, lookup)

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
    "San Francisco Public Defender": "http://sfpublicdefender.org/services/clean-slate/",
    "Contra Costa Public Defender": "http://co.contra-costa.ca.us/1555/Public-Defender",
    "Alameda Public Defender": "http://www.co.alameda.ca.us/defender/services/cleanslate.htm",
    "East Bay Community Law Center": "http://ebclc.org/need-services/clean-slate-services/",
    "clearmyrecord@codeforamerica.org": "mailto:clearmyrecord@codeforamerica.org",
    "(415) 301-6005": "tel:14153016005"
}

linkify = Linkifier(linkify_links)
