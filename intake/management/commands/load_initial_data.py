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
            if 'py' in ext and '__init__' not in base:
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

    def load_or_update_instance(self, model_class, data, lookup_keys):
        lookup_atts = {k: data[k] for k in lookup_keys}
        data.pop("pk", None) # don't try to update pk
        instance, created = model_class.objects.update_or_create(
            **lookup_atts,
            defaults=data)
        return instance

    def get_data_from_module(self, module_path):
        module = importlib.import_module(module_path)
        data = getattr(module, 'data', None)
        if not data:
            message = "`data` not found in `{}`".format(module.__name__)
            raise NoDataFoundError(message)
        return data

    def load_instances(self, data):
        model_class = self.import_class(data['model'])
        lookup_keys  = data.get("lookup_keys", ["pk"])
        for instance_data in data["instances"]:
            instance = self.load_or_update_instance(
                model_class, instance_data.copy(),
                lookup_keys=lookup_keys)
            message = "Successfully loaded '{}'".format(instance)
            self.stdout.write(message)
        self.loaded.append(data['model'])

    def dependencies_loaded(self, item):
        dependencies = item.get('depends_on', [])
        if dependencies:
            return all(
                k in self.loaded
                for k in dependencies)
        return True

    def assert_dependencies_exist_in_queue(self, item):
        dependencies = item['depends_on']
        class_names_in_queue = [
            m['model'] for m in self.queue
        ]
        for other in dependencies:
            if other not in class_names_in_queue:
                message = "`{}` not found in {}".format(
                    other, class_names_in_queue)
                raise ClassNotFoundError(message)

    def load_modules(self, paths):
        self.loaded = []
        self.queue = [
            self.get_data_from_module(p)
            for p in paths
            ]
        while self.queue:
            item = self.queue.pop(0)
            if self.dependencies_loaded(item):
                self.load_instances(item)
            else:
                self.assert_dependencies_exist_in_queue(item)
                self.queue.append(item)

    def handle(self, *args, **options):
        self.stdout.write("Loading initial data")
        data_import_paths = self.get_files_in_initial_data_folder()
        self.load_modules(data_import_paths)
        self.stdout.write("Finished loading data")
