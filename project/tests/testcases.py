import json
from django.test import TestCase as DjangoTestCase
from httmock import HTTMock, all_requests, response


@all_requests
def response_content(url, request):
    if url.netloc == 'api.mailgun.net':
        headers = {'content-type': 'application/json'}
        content = json.dumps({
            "address": "cmrtestuser@gmail.com",
            "did_you_mean": None,
            "is_disposable_address": False,
            "is_role_address": False,
            "is_valid": True,
            "mailbox_verification": 'true',
            "parts": {
                "display_name": None,
                "domain": "gmail.com",
                "local_part": "cmrtestuser"
            }
        })
        return response(200, content, headers, None, 5, request)
    else:
        return response(200)


class TestCase(DjangoTestCase):
    """This Base TestCase will mock out all outgoing requests to external URLs
        that are made using the requests library.

        By default, any request will return a blank 200 OK mock HTTP response.

        response_content can be edited to create custom responses, but this
        should only be done if local patching in tests is insufficient.
    """
    def run(self, result=None):
        with HTTMock(response_content) as httmock:
            self.httmock = httmock
            super().run(result)
