from django.db import transaction
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db.models.deletion import ProtectedError
from intake.tests.factories import VisitorFactory
from partnerships.tests.factories import PartnershipLeadFactory


class TestPartnershipLead(TestCase):

    def test_visitor_deletion(self):
        visitor = VisitorFactory()
        PartnershipLeadFactory(visitor=visitor)
        with self.assertRaises(ProtectedError):
            visitor.delete()

    def test_message_not_required(self):
        lead = PartnershipLeadFactory(message='')
        self.assertEqual(lead.message, '')

    def test_required_fields(self):
        for attr in ('visitor', 'name', 'email', 'organization_name'):
            # without transaction.atomic django chokes on too many errors
            # in the single transaction used for this test method
            with transaction.atomic():
                with self.assertRaises(IntegrityError):
                    PartnershipLeadFactory(**{attr: None})
