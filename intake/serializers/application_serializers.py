from collections import OrderedDict
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


class ApplicationCSVDownloadSerializer(serializers.ModelSerializer):

    def to_representation(self, app, *args, **kwargs):
        app_fields = super().to_representation(app, *args, **kwargs)
        display_form, letter = get_display_form_for_application(app)
        data = OrderedDict(id=app.form_submission_id)
        data['Link'] = app.form_submission.get_external_url()
        data['Application Date'] = \
            app.form_submission.get_local_date_received('%m/%d/%Y')
        for field in display_form.get_usable_fields():
            data[field.get_display_label()] = field.get_display_value()
        for key, value in app_fields.items():
            data[key] = value
        if letter:
            for field in letter.get_usable_fields():
                data[field.get_display_label()] = field.get_display_value()
        return data

    class Meta:
        model = models.Application
        fields = [
            'was_transferred_out',
            'has_been_opened'
        ]
