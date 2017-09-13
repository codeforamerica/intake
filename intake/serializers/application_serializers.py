from intake import models
from rest_framework import serializers
from .status_update_serializer import MinimalStatusUpdateSerializer
from intake.services.display_form_service import \
    get_display_form_for_application


class LatestStatusBase(serializers.ModelSerializer):

    def to_representation(self, *args, **kwargs):
        data = super().to_representation(*args, **kwargs)
        sorted_status_updates = sorted(
            data.get('status_updates', []), key=lambda d: d['updated'],
            reverse=True)
        latest_status = \
            sorted_status_updates[0] if sorted_status_updates else None
        data.update(latest_status=latest_status)
        return data


class ApplicationFollowupListSerializer(LatestStatusBase):
    organization = serializers.SlugRelatedField(
        read_only=True, slug_field='slug')
    status_updates = MinimalStatusUpdateSerializer(many=True)

    class Meta:
        model = models.Application
        fields = [
            'organization',
            'status_updates'
        ]


class ApplicationAutocompleteSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Application
        fields = ['name', 'url']

    def get_name(self, instance):
        return instance.form_submission.get_full_name()

    def get_url(self, instance):
        return instance.form_submission.get_absolute_url()


class ApplicationExcelDownloadSerializer(serializers.ModelSerializer):

    def to_representation(self, *args, **kwargs):
        # TODO: datetimes to PT
        data = super().to_representation(*args, **kwargs)
        display_form, letter = get_display_form_for_application(args[0])
        data.update({
            field.get_display_label(): field.get_display_value()
            for field in display_form.get_usable_fields()})
        if letter:
            data.update(letter.cleaned_data)
        return data

    class Meta:
        model = models.Application
        fields = '__all__'
