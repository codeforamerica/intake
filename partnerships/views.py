from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib import messages
from intake import tasks
import intake.services.events_service as EventsService
from intake.views.base_views import GlobalTemplateContextMixin
from partnerships.forms import PotentialPartnerLeadForm


class Home(GlobalTemplateContextMixin, TemplateView):
    template_name = "partnerships.jinja"


class Contact(GlobalTemplateContextMixin, FormView):
    template_name = "partnerships-contact.jinja"
    form_class = PotentialPartnerLeadForm
    success_message_template = str(
        'Thanks for reaching out! Your message has been sent to our '
        'partnerships team at '
        '<a href="mailto:{partnerships_lead_inbox}">'
        '{partnerships_lead_inbox}</a>. '
        'We will get back to you shortly.')

    def send_email(self, data):
        subject = 'New partnership lead from {}'.format(
            data['organization_name'])
        header = '\n'.join([
            'Email: "{email}"',
            'Name: "{name}"',
            'Organization: "{organization_name}"']).format(**data)
        tasks.send_email(
            subject=subject,
            message='\n\n'.join(
                [header, data.get('message', '')]
            ),
            from_email=settings.MAIL_DEFAULT_SENDER,
            recipient_list=[settings.PARTNERSHIPS_LEAD_INBOX]
        )

    def form_valid(self, form):
        partnership_lead = form.save(commit=False)
        partnership_lead.visitor = self.request.visitor
        partnership_lead.save()
        self.send_email(form.cleaned_data)
        EventsService.partnership_interest_submitted(self, partnership_lead)
        success_message = self.success_message_template.format(
            partnerships_lead_inbox=settings.PARTNERSHIPS_LEAD_INBOX)
        messages.success(self.request, success_message, extra_tags='safe')
        return redirect(reverse('partnerships-home'))


home = Home.as_view()
contact = Contact.as_view()
