from django.test import Client



class CsrfClient(Client):

    def __init__(self, **defaults):
        super().__init__(enforce_csrf_checks=True, **defaults)

    def fill_form(self, url, **data):
        follow = data.pop('follow', False)
        response = self.get(url)
        # if csrf protected, get the token
        csrf_token = response.cookies['csrftoken'].value
        data.update(csrfmiddlewaretoken=csrf_token)
        return self.post(url, data, follow=follow)