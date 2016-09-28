import datetime
from rest_framework import serializers
from intake import models
from formation.field_types import YES, NO

THIS_YEAR = datetime.datetime.now().year


class DictField(serializers.Field):
    """A read only field for serializing submission answers
    """
    def to_representation(self, obj):
        keys = getattr(self, 'keys', None)
        if keys:
            return {
                key: value
                for key, value in obj.items()
                if key in keys
                }
        return obj


class CityField(serializers.Field):
    def to_representation(self, obj):
        address = obj.get('address')
        if address:
            city = address.get('city')
            state = address.get('state')
            return ', '.join([n for n in (city, state) if n])


class AgeField(serializers.Field):
    def to_representation(self, obj):
        dob = obj.get('dob')
        if dob:
            year = dob.get('year')
            if year:
                return THIS_YEAR - int(year)


class DictKeyField(serializers.Field):
    def __init__(self, key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key

    def to_representation(self, dictionary):
        return dictionary.get(self.key)


class YesNoAnswerField(DictKeyField):

    def to_representation(self, dictionary):
        value = super().to_representation(dictionary)
        if value == YES:
            return True
        elif value == NO:
            return False
        return value


class SubmissionAnswersField(DictField):
    keys = [
            'contact_preferences',
            'monthly_income',
            'us_citizen',
            'being_charged',
            'serving_sentence',
            'on_probation_parole',
            'currently_employed',
        ]


class EventTypeField(serializers.Field):
    event_name = None
    reducer = len

    def __init__(self, *args, **kwargs):
        base_kwargs = {
            'source': 'events'
        }
        base_kwargs.update(kwargs)
        super().__init__(*args, **base_kwargs)

    def filter(self, events):
        return events.filter(name=self.event_name)

    def reduce(self, events):
        return self.reducer(events)

    def to_representation(self, events):
        return self.reduce(self.filter(events))


class HasEventField(EventTypeField):

    def to_representation(self, events):
        return bool(super().to_representation(events))


class EventTimeField(EventTypeField):
    event_name = None

    def reduce(self, events):
        times = events.values_list('time', flat=True)
        if times:
            return max(times).isoformat()


class EventDataKeyField(EventTypeField):
    key = None

    def reduce(self, events):
        data = events.values_list('data', flat=True)
        values = [
            datum.get(self.key)
            for datum in data
            if datum and self.key in datum]
        return next(iter(values), None)


class Started(EventTimeField):
    event_name = models.ApplicationEvent.APPLICATION_STARTED


class Finished(EventTimeField):
    event_name = models.ApplicationEvent.APPLICATION_SUBMITTED


class HadErrors(HasEventField):
    event_name = models.ApplicationEvent.APPLICATION_ERRORS


class IPAddress(EventDataKeyField):
    event_name = models.ApplicationEvent.APPLICATION_STARTED
    key = 'ip'


class Referrer(EventDataKeyField):
    event_name = models.ApplicationEvent.APPLICATION_STARTED
    key = 'referrer'
