from django.test import SimpleTestCase, RequestFactory
from . import views

class RobotsTestCase(SimpleTestCase):

    def test_robots_txt_factory(self):
        allow = ['one', 'two']
        view = views.robots_view(allow)
        response = view({})
        self.assertContains(response, 'Allow: one')
        self.assertContains(response, 'Allow: two')

