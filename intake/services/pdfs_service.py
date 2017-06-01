from intake import models
from user_accounts.models import Organization
import intake.services.applications_service as AppsService



def build_unread_apps_pdf(app_ids=None):
    pass
    



def get_or_create_prebuilt_pdf():
    sf_pubdef = Organization.objects.get(slug='sf_pubdef')
    unread_applications = AppsService.get_unread_applications_for_org(
        sf_pubdef)
    # do these apps have an up-to-date-prefilled-pdf?
    prebuilt = models.PrebuiltMultiAppPDF.objects.filter(
        organization=sf_pubdef)
    unread_app_ids = unread_applications.values_list('id', flat=True)
    prebuilt_app_ids = prebuilt.applications.values_list('id', flat=True)
    has_correct_prebuilt_apps = set(unread_app_ids) == set(prebuilt_app_ids)
    if not has_correct_prebuilt_apps:
        prebuild_unread_apps_pdf(unread_app_ids, prebuilt)


def concat_pdfs_for_apps(applications):
    """
    This is a blocking call to
    """
    pass
