import csv
import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden

from intake.models import FormSubmission


@login_required
def email_csv(request):
    if not request.user.has_perm('clips.change_clip'):
        return HttpResponseForbidden()
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d-%H-%M")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename="cmr-emails-%s.tsv"' % now_str
    writer = csv.writer(response, delimiter='\t', quoting=csv.QUOTE_MINIMAL)

    headers = [
        'ID',
        'Submission date',
        'Email',
        'Phone number',
        'Prefers Email',
        'Prefers SMS',
        'Counties',
        'How did you hear',
        'Anything else we should know',
        'Last Status Update At',
        'Last Status',
        'Is Eligible',
        'Is Granted',
        'Notes',
        'Tags'
    ]

    writer.writerow(headers)
    subs = FormSubmission.objects.all()

    for sub in subs:
        for app in sub.applications.all():
            granted = app.status_updates.filter(
                status_type__slug='granted').count() > 0

            eligible = app.status_updates.filter(
                status_type__slug='eligible').count() > 0

            last_status = app.status_updates.order_by('-updated').first()
            if last_status:
                last_status_name = last_status.status_type.display_name
                last_status_date = last_status.updated.strftime("%Y-%m-%d")
            else:
                last_status_name = None
                last_status_date = None

            columns = [
                sub.id,
                sub.date_received.strftime("%Y-%m-%d"),
                sub.email,
                sub.phone_number,
                'prefers_email' in sub.contact_preferences,
                'prefers_sms' in sub.contact_preferences,
                app.organization.name,
                sub.how_did_you_hear,
                sub.additional_information,
                last_status_date,
                last_status_name,
                eligible,
                granted
            ]

            writer.writerow(columns)
    return response
