import datetime
from rest_framework import serializers
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


class AnswerKeyField(serializers.Field):
    def __init__(self, key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key

    def to_representation(self, answers):
        return answers.get(self.key)


class YesNoAnswerField(AnswerKeyField):

    def to_representation(self, answers):
        value = super().to_representation(answers)
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
