import statistics
import urllib
from collections import Counter
from rest_framework import serializers


def parse_url_host(full_url):
    return urllib.parse.urlparse(full_url).netloc


def get_duration(start, end):
    tdelta = end - start
    return tdelta.total_seconds()


def seconds_to_complete(apps):
    durations = [
            get_duration(app['started'], app['finished'])
            for app in apps]
    has_negatives = any([d < 0 for d in durations])
    if has_negatives:
        import ipdb; ipdb.set_trace()
    return durations


def truthy_values_filter(apps, *keys):
    for app in apps:
        if all([app.get(key) for key in keys]):
            yield app


class ApplicationAggregateField(serializers.Field):
    reducer = len

    def get_default_value(self):
        return None

    def filter(self, applications):
        return applications

    def reduce(self, applications):
        return self.reducer(applications)

    def to_representation(self, applications):
        filtered = list(self.filter(applications))
        if not filtered:
            return self.get_default_value()
        return self.reduce(filtered)


class FinishedCountField(ApplicationAggregateField):

    def get_default_value(self):
        return 0

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
    def get_default_value(self):
        return {}

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
