from django.test import TestCase
from user_accounts import models


class TestAddress(TestCase):

    def test_can_create_without_walk_in_hours(self):
        a_pubdef = models.Organization.objects.get(slug='a_pubdef')
        address = models.Address(
            organization=a_pubdef,
            name='Oakland Office',
            text="545 4th St\nOakland, CA\n94607")
        address.save()
        self.assertTrue(address.id)

    def test_can_create_with_walk_in_hours(self):
        a_pubdef = models.Organization.objects.get(slug='a_pubdef')
        address = models.Address(
            organization=a_pubdef,
            name='Oakland Office',
            walk_in_hours="Every Tuesday, from 2pm to 4pm",
            text="545 4th St\nOakland, CA\n94607")
        address.save()
        self.assertTrue(address.id)

    def can_get_addresses_of_organization(self):
        a_pubdef = models.Organization.objects.get(slug='a_pubdef')
        address = models.Address(
            organization=a_pubdef,
            name='Oakland Office',
            walk_in_hours="Every Tuesday, from 2pm to 4pm",
            text="545 4th St\nOakland, CA\n94607")
        address.save()
        self.assertEqual(address.organization, a_pubdef)
        self.assertListEqual(
            list(a_pubdef.addresses.all()),
            [address])
