from django.test import Client


class CsrfClient(Client):
    def __init__(self, **defaults):
        super().__init__(enforce_csrf_checks=True, **defaults)