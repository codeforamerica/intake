from django.conf import settings
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib import messages
from intake import tasks
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
        subject = 'New Partnership Lead from {}'.format(
            data['organization_name'])
        header = '\n'.join([
            key.title() + ': ' + data[key]
            for key in ('email', 'name', 'organization_name')
            ])
        tasks.send_email.delay(
            subject=subject,
            message='\n\n'.join(
                [header, data.get('message', '')]
            ),
            from_email=settings.MAIL_DEFAULT_SENDER,
            recipient_list=[settings.PARTNERSHIPS_LEAD_INBOX]
        )

    def form_valid(self, form):
        form.save()
        self.send_email(form.cleaned_data)
        success_message = self.success_message_template.format(
            partnerships_lead_inbox=settings.PARTNERSHIPS_LEAD_INBOX)
        messages.success(self.request, success_message, extra_tags='safe')
        return redirect(reverse('partnerships-home'))


home = Home.as_view()
contact = Contact.as_view()
