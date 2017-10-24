from django.core.management import call_command
from django.core.management.base import BaseCommand

from intake.models import Application
from intake.services.pdf_service import fill_pdf_for_application, \
    update_pdf_bundle_for_san_francisco
from intake.tests.mock import build_seed_submissions, fillable_pdf
from user_accounts.tests.mock import create_seed_users, serialize_seed_users


class Command(BaseCommand):
    help = 'Generates new json sample fixtures'

    def handle(self, *args, **options):
        call_command('flush', interactive=False)
        self.stdout.write(
            self.style.SUCCESS("Destroyed all existing data"))
        call_command('load_essential_data')
        self.stdout.write(
            self.style.SUCCESS(
                "Loaded organizations, counties, groups, & permissions "
                "from fixtures"))
        create_seed_users()
        self.stdout.write(
            self.style.SUCCESS("Created fake user profiles"))
        serialize_seed_users()
        self.stdout.write(
            self.style.SUCCESS(
                "Saved to mock_profiles fixture"))
        fillable_pdf()
        self.stdout.write(
            self.style.SUCCESS(
                "Load fake fillable pdf"))
        build_seed_submissions()
        self.stdout.write(
            self.style.SUCCESS(
                "Created fake submissions, bundles, and transfers "
                "and saved them to fixture files"))
        for app_id in Application.objects.filter(
                    organization__slug='sf_pubdef'
                ).values_list('id', flat=True):
            fill_pdf_for_application(app_id)
        update_pdf_bundle_for_san_francisco()
        self.stdout.write(
            self.style.SUCCESS(
                "Pre-filled PDFs for San Francisco, including pdf bundle of "
                "unread apps"))
