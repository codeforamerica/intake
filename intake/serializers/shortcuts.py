from .applicant_serializer import ApplicantMixpanelSerializer
from .request_serializer import RequestSerializer
from .view_serializer import ViewMixpanelSerializer


def mixpanel_applicant_data(applicant):
    return ApplicantMixpanelSerializer(applicant).data


def mixpanel_request_data(request):
    return RequestSerializer(request).data


def mixpanel_view_data(view):
    return ViewMixpanelSerializer(view).data
