from twilio.twiml.voice_response import VoiceResponse
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.templatetags.static import static
from phone.validators import is_valid_twilio_request
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from intake.constants import PACIFIC_TIME


def get_time_received():
    return timezone.now().astimezone(PACIFIC_TIME).strftime(
            "%-m/%-d/%Y %-I:%M %p %Z")


class TwilioBaseView(View):

    def post(self, request):
        """Validate if this request is signed by Twilio
            https://www.twilio.com/docs/api/security
        """
        if is_valid_twilio_request(request):
            return self.post_valid(request)
        else:
            raise Http404

    def post_valid(self, request):
        raise NotImplementedError("Should be overwritten in subclasses")


class HandleIncomingCallView(TwilioBaseView):
    voicemail_static_path = 'voicemail/CMR_voicemail_greeting.mp3'

    def post_valid(self, request):
        """Expects a POST request from Twilio, and return a response directing
        Twilio to play the greeting mp3 and post the recorded response to
        the handle voicemail URL
        """
        response = VoiceResponse()
        self.static_greeting_path = static(self.voicemail_static_path)
        self.record_voicemail_url = request.build_absolute_uri(
            reverse('phone-handle_new_message')).replace('http:', 'https:')
        response.play(self.static_greeting_path)
        response.record(action=self.record_voicemail_url, method='POST')
        return HttpResponse(response)


class HandleVoicemailRecordingView(TwilioBaseView):

    def post_valid(self, request):
        """
        This expects a POST reqest from Twilio with a link to a
        new voicemail recording
        """
        recording_url = request.POST.get('RecordingUrl', '')
        from_number = request.POST.get("From", '')
        # TODO: add an event to trigger, and try to log in mixpanel that
        # someone called
        time_received = get_time_received()
        body = str(
            "New voicemail from {}\n\n"
            "Received: {}\n\n"
            "Listen to the recording at\n    {}").format(
                from_number, time_received, recording_url)
        send_mail(
            subject="New voicemail {}".format(time_received),
            message=body,
            from_email=settings.MAIL_DEFAULT_SENDER,
            recipient_list=[settings.VOICEMAIL_NOTIFICATION_EMAIL])
        return HttpResponse()


record = csrf_exempt(HandleIncomingCallView.as_view())
handle_new_message = csrf_exempt(HandleVoicemailRecordingView.as_view())
