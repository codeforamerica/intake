import statistics
import urllib
import dateutil
from collections import Counter
from rest_framework import serializers


def parse_url_host(full_url):
    return urllib.parse.urlparse(full_url).netloc


def isostrings_to_duration(start, end):
    tdelta = dateutil.parser.parse(end) - dateutil.parser.parse(start)
    return tdelta.total_seconds()


def seconds_to_complete(apps):
    return [
        isostrings_to_duration(app['started'], app['finished'])
        for app in apps]


def truthy_values_filter(apps, *keys):
    for app in apps:
        if all([app.get(key) for key in keys]):
            yield app


class ApplicationAggregateField(serializers.Field):
    reducer = len

    def filter(self, applications):
        return applications

    def reduce(self, applications):
        return self.reducer(applications)

    def to_representation(self, applications):
        return self.reduce(list(self.filter(applications)))


class FinishedCountField(ApplicationAggregateField):
    def filter(self, applications):
        return truthy_values_filter(applications, 'finished')


class MeanCompletionTimeField(ApplicationAggregateField):
    def filter(self, applications):
        """Only include applications that have both finished and started times
        """
        return truthy_values_filter(
            applications, 'finished', 'started')

    def reduce(self, applications):
        return statistics.mean(seconds_to_complete(applications))


class MedianCompletionTimeField(MeanCompletionTimeField):
    def reduce(self, applications):
        return statistics.median(seconds_to_complete(applications))


class MajorSourcesField(ApplicationAggregateField):
    def filter(self, applications):
        """Only include applications that have a referrer attribute
        """
        return truthy_values_filter(applications, 'finished', 'referrer')

    def reduce(self, applications):
        """return a dictionary of referrer_url: fraction_of_finished_apps
        """
        total = len(applications)
        referrer_counts = Counter([
            parse_url_host(app['referrer']) for app in applications])
        return {
            referrer: count / total
            for referrer, count in referrer_counts.items()
        }


class DropOffField(ApplicationAggregateField):
    def filter(self, applications):
        return truthy_values_filter(applications, 'started')

    def reduce(self, applications):
        """Return the number of finished apps as a fraction of started apps
        """
        total = len(applications)
        finished = len(list(truthy_values_filter(applications, 'finished')))
        return finished / total


class MultiCountyField(ApplicationAggregateField):

    def reduce(self, applications):
        total = len(applications)
        multicounty = len(list(
            truthy_values_filter(applications, 'is_multicounty')))
        return multicounty / total
