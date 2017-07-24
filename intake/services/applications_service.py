from django.db.models import Q
from intake import models, serializers, notifications, tasks
from intake.services import events_service as EventsService
from . import pagination


def get_applications_for_org(organization):
    # preselect_tables are joined using `select_related()` by following single
    # foreign keys. They are captured in one query along with the main model.
    preselect_tables = [
        'form_submission'
    ]
    # prefetch_tables are brought inusing `prefetch_related()`. Each of these
    # become a separate query to pull in related objects from other tables.
    # Most of these are reverse foreign keys, and it may be possible to further
    # optimize these into less queries.
    # https://blog.roseman.org.uk/2010/01/11/django-patterns-part-2-efficient-reverse-lookups/
    prefetch_tables = [
        'status_updates',
        'status_updates__status_type',
    ]
    if organization.can_transfer_applications:
        prefetch_tables += [
            'incoming_transfers',
            'incoming_transfers__new_application__organization',
            'incoming_transfers__status_update',
            'incoming_transfers__status_update__application',
            'incoming_transfers__status_update__author__profile__organization',
            'incoming_transfers__status_update__author',
            'incoming_transfers__status_update__author__profile',
        ]
    qset = models.Application.objects.filter(
        organization=organization
    ).select_related(*preselect_tables).prefetch_related(*prefetch_tables)
    return qset.order_by('-created').distinct()

UNREAD_APPLICATIONS_FILTER_KWARGS = dict(
    has_been_opened=False, status_updates__isnull=True)


NEEDS_STATUS_UPDATE_FILTER_KWARGS = dict(status_updates__isnull=True)


def get_unread_applications_for_org(organization):
    return get_applications_for_org(organization).filter(
        **UNREAD_APPLICATIONS_FILTER_KWARGS)


def get_applications_for_org_user(user, page_index, **filters):
    """Paginates and serializes applications for an org user
    """
    organization = user.profile.organization
    query = get_applications_for_org(organization)
    if filters:
        query = query.filter(**filters)
    serializer = serializers.ApplicationIndexSerializer
    if organization.can_transfer_applications:
        serializer = \
            serializers.ApplicationIndexWithTransfersSerializer
    return pagination.get_serialized_page(query, serializer, page_index)


def get_all_applications_for_org_user(user, page_index):
    return get_applications_for_org_user(user, page_index)


def get_unread_applications_for_org_user(user, page_index):
    return get_applications_for_org_user(
        user, page_index, **UNREAD_APPLICATIONS_FILTER_KWARGS)


def get_applications_needing_updates_for_org_user(user, page_index):
    return get_applications_for_org_user(
        user, page_index, **NEEDS_STATUS_UPDATE_FILTER_KWARGS)


def get_status_updates_for_org_user(application):
    # note: this only returns status updates for the latest transfer
    #   if an app has multiple transfers, older ones will be overlooked
    are_updates_for_this_app = Q(application=application)
    queryset = models.StatusUpdate.objects.filter(are_updates_for_this_app)
    prefetch_tables = [
        'notification',
        'status_type',
        'next_steps',
        'author__profile',
        'author__profile__organization']
    if application.organization.can_transfer_applications:
        transfer = application.incoming_transfers.order_by('-created').first()
        if transfer:
            are_updates_prior_to_a_transfer = Q(
                application_id=transfer.status_update.application_id,
                updated__lte=transfer.status_update.updated)
            queryset = models.StatusUpdate.objects.filter(
                are_updates_for_this_app | are_updates_prior_to_a_transfer
            )
            prefetch_tables.extend([
                'transfer',
                'transfer__status_update',
                'transfer__status_update__author__profile',
                'transfer__status_update__author__profile__organization',
                'transfer__new_application__organization'])
    return queryset.prefetch_related(*prefetch_tables).order_by('-updated')


def get_status_updates_for_staff_user(application):
    return models.StatusUpdate.objects.filter(
        application__form_submission__id=application.form_submission.id
    ).prefetch_related(
        'notification',
        'status_type',
        'next_steps',
        'author__profile',
        'author__profile__organization',
        'transfer',
        'transfer__status_update',
        'transfer__status_update__author__profile',
        'transfer__status_update__author__profile__organization',
        'transfer__new_application__organization'
    ).order_by('-updated')


def get_serialized_application_history_events(application, user):
    if user.is_staff:
        status_updates = get_status_updates_for_staff_user(application)
    else:
        status_updates = get_status_updates_for_org_user(application)
    return serializers.StatusUpdateSerializer(status_updates, many=True).data


def filter_to_org_if_not_staff(apps, user):
    if not user.is_staff:
        return apps.filter(
            organization_id=user.profile.organization_id)
    return apps


def coerce_possible_ids_to_apps(maybe_ids):
    if maybe_ids:
        if isinstance(maybe_ids[0], int):
            return models.Application.objects.filter(id__in=maybe_ids)
    return maybe_ids


def handle_apps_opened(view, apps, send_slack_notification=True):
    apps = coerce_possible_ids_to_apps(apps)
    EventsService.apps_opened(view, apps)
    EventsService.user_apps_opened(view, apps)
    for app in apps:
        should_be_marked = \
            view.request.user.profile.organization_id == app.organization_id
        if should_be_marked:
            app.has_been_opened = True
            app.save()
            tasks.remove_application_pdfs.delay(app.id)
        if send_slack_notification:
            notifications.slack_submissions_viewed.send(
                submissions=[app.form_submission], user=view.request.user,
                bundle_url=app.form_submission.get_external_url())


def get_valid_application_ids_from_set(application_ids):
    return models.Application.objects.filter(
        id__in=application_ids).values_list('id', flat=True)


def get_unread_apps_per_org_count(organization):
    return models.Application.objects.filter(
        organization=organization, **UNREAD_APPLICATIONS_FILTER_KWARGS).count()


def get_needs_update_apps_per_org_count(organization):
    return models.Application.objects.filter(
        organization=organization, **NEEDS_STATUS_UPDATE_FILTER_KWARGS).count()


def get_all_apps_per_org_count(organization):
    return models.Application.objects.filter(
        organization=organization).count()
