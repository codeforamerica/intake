from intake.middleware import MiddlewareBase
from easyaudit.middleware.easyaudit import clear_request


class ClearRequestMiddleware(MiddlewareBase):

    def process_response(self, response):
        clear_request()
