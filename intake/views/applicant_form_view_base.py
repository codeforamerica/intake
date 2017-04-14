from django.views.generic.edit import FormView
from django.utils.translation import ugettext as _
from intake import utils
import intake.services.events_service as EventsService
import intake.services.messages_service as MessagesService


ERROR_MESSAGE = _(str(
    "There were some problems with your application. "
    "Please check the errors below."))


class ApplicantFormViewBase(FormView):
    session_key = 'form_in_progress'

    def form_valid(self, form):
        EventsService.log_form_page_complete(
            self.request, page_name=self.__class__.__name__)
        utils.save_form_data_to_session(
            self.request, self.session_key, form.data)
        return super().form_valid(form)

    def form_invalid(self, form):
        MessagesService.flash_errors(
            self.request, ERROR_MESSAGE, *form.non_field_errors())
        EventsService.log_form_validation_errors(
            self.request, errors=form.get_serialized_errors())
        return super().form_invalid(form)

    def finalize_application(self):
        # save submission, send confirmations, logs events
        pass
