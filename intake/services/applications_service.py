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
