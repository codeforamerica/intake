from django.test import TestCase

from intake.models import Visitor


class TestVisitor(TestCase):

    def test_init_visitor_with_no_info(self):
        visitor = Visitor()
        visitor.save()
        self.assertTrue(visitor.id)
        self.assertTrue(visitor.first_visit)

    def test_save_with_source_and_referrer(self):
        visitor = Visitor(
            source='prop47fair',
            referrer='www.google.com')
        visitor.save()
        self.assertTrue(visitor.id)
        self.assertTrue(visitor.first_visit)
