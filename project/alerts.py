from django.core import mail
from django.conf import settings


def send_email_to_admins(subject, message):
    mail.send_mail(
        subject=subject, message=message,
        from_email=settings.MAIL_DEFAULT_SENDER,
        recipient_list=[email for name, email in settings.ADMINS])
