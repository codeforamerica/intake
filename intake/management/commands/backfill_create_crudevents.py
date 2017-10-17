from easyaudit.models import CRUDEvent
from intake.models import FormSubmission
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = str(
        "This backfills CRUDEvents with type CREATE for FormSubmissions that "
        "do not have them (were submitted before easy-audit was added).")

    def handle(self, *args, **kwargs):
        form_sub_ids_with_crud_events = set(
            CRUDEvent.objects.filter(
                content_type__model='formsubmission'
            ).values_list('object_id', flat=True))
        subs_without_events = FormSubmission.objects.exclude(
            id__in=form_sub_ids_with_crud_events)
        for sub in subs_without_events:
            CRUDEvent.objects.create(
                event_type=CRUDEvent.CREATE,
                object_repr=str(sub),
                object_json_repr=serializers.serialize("json", [sub]),
                content_type=ContentType.objects.get_for_model(sub),
                object_id=sub.pk,
                user=None,
                datetime=timezone.now(),
                user_pk_as_string=None
            )
        self.stdout.write("Created CRUDEvents for {} FormSubmissions".format(
            len(subs_without_events)
        ))
