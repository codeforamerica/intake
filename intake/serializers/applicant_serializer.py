from rest_framework import serializers
from intake.serializers.fields import ChainableAttributeField


class ApplicantMixpanelSerializer(serializers.Serializer):
    """This serializes user information from an applicant instance
    """
    applicant_source = ChainableAttributeField('visitor.source')
    applicant_referrer = ChainableAttributeField('visitor.referrer')
