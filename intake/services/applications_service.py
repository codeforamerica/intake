from django.db.models import Q
from intake import models, serializers
from . import pagination


def get_applications_for_org(organization):
    prefetch_tables = [
        'form_submission',
        'status_updates',
        'status_updates__status_type',
    ]
    if organization.can_transfer_applications:
        prefetch_tables += [
            'incoming_transfers',
            'incoming_transfers__status_update',
            'incoming_transfers__status_update__application',
            'incoming_transfers__status_update__application__organization',
            'incoming_transfers__status_update__author',
            'incoming_transfers__status_update__author__profile',
        ]
    return models.Application.objects.filter(
            organization=organization
        ).prefetch_related(*prefetch_tables).order_by('-created').distinct()


def get_applications_index_for_org_user(user, page_index):
    """Paginates and serializes applications for an org user
    """
    # this is two queries
    organization = user.profile.organization
    query = get_applications_for_org(organization)
    serializer = serializers.ApplicationIndexSerializer
    if organization.can_transfer_applications:
        serializer = \
            serializers.ApplicationIndexWithTransfersSerializer
    return pagination.get_serialized_page(query, serializer, page_index)


def transfer_application(author, application, to_organization, reason):
    """Transfers an application from one organization to another
    """
    transfer_status_update = models.StatusUpdate(
        status_type_id=models.status_type.TRANSFERRED,
        author_id=author.id,
        application=application
    )
    transfer_status_update.save()
    new_application = models.Application(
        form_submission_id=application.form_submission_id,
        organization=to_organization)
    new_application.save()
    transfer = models.ApplicationTransfer(
        status_update=transfer_status_update,
        new_application=new_application,
        reason=reason)
    transfer.save()
    application.was_transferred_out = True
    application.save()
    return transfer


def get_status_updates_for_org_user(application):
    # note: this only returns status updates for the latest transfer
    #   if an app has multiple transfers, older ones will be overlooked
    are_updates_for_this_app = Q(
        application=application)
    queryset = models.StatusUpdate.objects.filter(are_updates_for_this_app)
    prefetch_tables = [
        'notification',
        'status_type',
        'next_steps',
        'author__profile',
        'author__profile__organization',
    ]
    if application.organization.can_transfer_applications:
        transfer = application.incoming_transfers.order_by('-created').first()
        if transfer:
            are_updates_prior_to_a_transfer = Q(
                application_id=transfer.status_update.application_id,
                updated__lte=transfer.status_update.updated)
            queryset = models.StatusUpdate.objects.filter(
                are_updates_for_this_app | are_updates_prior_to_a_transfer
            )
            prefetch_tables.append('transfer')
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
        'transfer'
    ).order_by('-updated')


def get_serialized_application_history_events(application, user):
    if user.is_staff:
        status_updates = get_status_updates_for_staff_user(application)
    else:
        status_updates = get_status_updates_for_org_user(application)
    return serializers.StatusUpdateSerializer(status_updates, many=True).data
