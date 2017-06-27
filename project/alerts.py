from django.conf import settings
from intake import tasks


def send_email_to_admins(subject, message):
    """Asynchronously sends an email alert to all ADMINs in settings
    """
    tasks.send_email.delay(
        subject=subject, message=message,
        from_email=settings.MAIL_DEFAULT_SENDER,
        recipient_list=[email for name, email in settings.ADMINS])
