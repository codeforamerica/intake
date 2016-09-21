from django.test import Client


class CsrfClient(Client):

    def __init__(self, **defaults):
        super().__init__(enforce_csrf_checks=True, **defaults)

    def get_csrf_token(self, response):
        return response.cookies['csrftoken'].value

    def fill_form(self, url, csrf_token=None, headers=None, **data):
        if not csrf_token:
            response = self.get(url)
            csrf_token = self.get_csrf_token(response)
        follow = data.pop('follow', False)
        data.update(csrfmiddlewaretoken=csrf_token)
        headers = headers or {}
        return self.post(url, data, follow=follow, **headers)
