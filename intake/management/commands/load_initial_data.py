import os
import importlib

from django.conf import settings
from django.core.management.base import BaseCommand


class NoDataFoundError(Exception):
    pass


class ClassNotFoundError(Exception):
    pass


class Command(BaseCommand):
    help = 'Imports data from an app folder called `initial_data`'

    def get_files_in_initial_data_folder(self):
        initial_data_path_fragments = [
            'intake', 'initial_data'
        ]
        folder_path = os.path.join(
            settings.REPO_DIR, 
            *initial_data_path_fragments)
        import_paths = []
        for filename in os.listdir(folder_path):
            base, ext = os.path.splitext(filename)
            if 'py' in ext:
                import_path = '.'.join([
                    *initial_data_path_fragments,
                    base])
                import_paths.append(import_path)
        return import_paths

    def import_class(self, class_path):
        *module_bits, class_name = class_path.split('.')
        module_path = '.'.join(module_bits)
        module = importlib.import_module(module_path)
        model_class = getattr(module, class_name, None)
        if not model_class:
            message = "Could not find `{}` in `{}`".format(
                class_name, module.__name__)
            raise ClassNotFoundError(message)
        return model_class

    def load_or_update_instance(self, model_class, data):
        pk = data.pop("pk")
        instance, created = model_class.objects.update_or_create(
            pk=pk,
            defaults=data)
        return instance

    def load_data_from_module(self, module):
        data = getattr(module, 'data', None)
        if not data:
            message = "`data` not found in `{}`".format(module.__name__)
            raise NoDataFoundError(message)
        model_class = self.import_class(data['model'])
        for instance_data in data["instances"]:
            instance = self.load_or_update_instance(model_class, instance_data)
            message = "Successfully loaded '{}'".format(instance)
            self.stdout.write(message)

    def handle(self, *args, **options):
        self.stdout.write("Loading initial data")
        data_import_paths = self.get_files_in_initial_data_folder()
        for import_path in data_import_paths:
            module = importlib.import_module(import_path)
        self.load_data_from_module(module)
        self.stdout.write("Finished loading data")
