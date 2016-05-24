from django.test import TestCase

from user_accounts.forms import InviteForm
from user_accounts.models import Organization, Invitation


class TestUserAccounts(TestCase):

    def have_some_orgs(self):
        if not getattr(self, 'orgs', None):
            self.orgs = [
                Organization(name=n)
                for n in ["Org A", "Org B"]
                ]
            for org in self.orgs:
                org.save()

    def test_invite_form_has_the_right_fields(self):
        self.have_some_orgs()
        form = InviteForm()
        email_field = form.fields['email']
        org_field = form.fields['organization']
        form_html = form.as_p()
        for org in self.orgs:
            self.assertIn(org.name, form_html)

    def test_invite_form_saves_correctly(self):
        self.have_some_orgs()
        form = InviteForm(dict(
            email="someone@example.com",
            organization=self.orgs[0].id
            ))
        self.assertTrue(form.is_valid())
        invite = form.save()
        qset = Invitation.objects.filter(
            email="someone@example.com",
            organization=self.orgs[0]
            )
        self.assertEqual(qset.first(), invite)


