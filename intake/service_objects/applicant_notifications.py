from intake import notifications, models, utils
from intake.constants import SMS, EMAIL

from intake.serializers.fields import ContactInfoByPreferenceField
from intake.exceptions import FrontAPIError


class ApplicantNotification:
    message_accessors = {}
    notification_type = None
    application_event_log_function = None

    def __init__(self, submission):
        self.sub = submission
        # errors is a key value store of contact methods
        # and errors for each method
        self.errors = {}
        self.successes = []
        # self.contact_methods is list of usable contact
        # methods for this submission
        self.contact_methods = []
        # self.contact_info holds the contact for each method
        self.contact_info = {}
        self.set_contact_methods()
        self.messages = []

    def get_message_accessor(self, method):
        return self.message_accessors[method]

    def filter_contact_methods(self, contact_method_keys):
        return contact_method_keys

    def set_contact_methods(self):
        self.contact_info = \
            dict(ContactInfoByPreferenceField().to_representation(
                self.sub.answers))
        self.contact_methods = self.filter_contact_methods([
            method
            for method, info in self.contact_info.items()
        ])
        self.contact_methods.sort()

    def get_context(self, contact_method=None):
        orgs = list(self.sub.organizations.all())
        orgs = utils.sort_orgs_in_default_order(orgs)
        organization_names = [
            org.name for org in orgs]
        county_names = [
            org.county.name for org in orgs]
        return dict(
            staff_name=utils.get_random_staff_name(),
            name=self.sub.answers['first_name'],
            county_names=county_names,
            organizations=orgs,
            organization_names=organization_names,
        )

    def get_notification_channel(self, method):
        return None

    def log_event_to_submission(self, contact_method, message_content):
        message_info = dict(
            contact_info={
                contact_method: self.contact_info[contact_method]
            },
            message_content=message_content)
        self.messages.append(message_info)
        self.application_event_log_function(
            self.sub.applicant_id, **message_info)

    def send_notification_message(self, contact_method):
        context = self.get_context(contact_method)
        notification_channel = self.get_notification_channel(contact_method)
        # notification_channel.render returns a namedtuple
        message_content = notification_channel.render(**context)._asdict()
        notification_channel.send(
            to=self.contact_info[contact_method],
            **context)
        self.log_event_to_submission(contact_method, message_content)

    def send_notifications_to_applicant(self):
        """Sends one or more notifications to the applicant
        """
        for method in self.contact_methods:
            try:
                self.send_notification_message(method)
                self.successes.append(method)
            except FrontAPIError as error:
                self.errors[method] = error

    def log_outcome_in_slack(self):
        if self.successes:
            notifications.slack_notification_sent.send(
                methods=[
                    method for method in self.contact_methods
                    if method not in self.errors
                ],
                notification_type=self.notification_type,
                submission=self.sub
            )
        if self.errors:
            notifications.slack_notification_failed.send(
                errors=self.errors,
                notification_type=self.notification_type,
                submission=self.sub)

    def send(self):
        self.send_notifications_to_applicant()
        self.log_outcome_in_slack()


class FollowupNotification(ApplicantNotification):
    notification_type = 'followup'
    message_accessors = {
        EMAIL: 'long_followup_message',
        SMS: 'short_followup_message',
    }
    application_event_log_function = models.ApplicationEvent.log_followup_sent

    def get_notification_channel(self, method):
        if method == EMAIL:
            return notifications.email_followup
        elif method == SMS:
            return notifications.sms_followup

    def filter_contact_methods(self, keys):
        """Followups should pick one method and prefer email.
        """
        for key in [EMAIL, SMS]:
            if key in keys:
                return [key]

    def get_context(self, contact_method):
        context = super().get_context()
        contact_method = self.contact_methods[0]
        followup_messages = [
            getattr(org, self.get_message_accessor(contact_method))
            for org in context['organizations']]
        context.update(
            followup_messages=followup_messages
            )
        return context


class ConfirmationNotification(ApplicantNotification):
    notification_type = 'confirmation'
    message_accessors = {
        EMAIL: 'long_confirmation_message',
        SMS: 'short_confirmation_message',
    }
    application_event_log_function = \
        models.ApplicationEvent.log_confirmation_sent

    def get_notification_channel(self, method):
        if method == EMAIL:
            return notifications.email_confirmation
        elif method == SMS:
            return notifications.sms_confirmation

    def filter_contact_methods(self, keys):
        return [key for key in keys if key in [EMAIL, SMS]]

    def get_context(self, contact_method):
        context = super().get_context()
        next_steps = [
            getattr(org, self.get_message_accessor(contact_method))
            for org in context['organizations']
        ]
        context.update(next_steps=next_steps)
        return context
