import os
from django.core import serializers


class FixtureDataMigration:
    """Loads data from a fixture

    `forward` loads the fixture
    `reverse` will delete all rows of the designated models
    """

    # fixture_files
    # should be a list of tuples:
    #   ('appname', 'fixture_file_name.json')
    fixture_files = []

    # model_classes
    # should be a list of tuples:
    #   ('appname', 'MyModel')
    model_classes = []

    @classmethod
    def fixture_path(cls, app_name, filename):
        file_path = os.path.join(app_name, 'fixtures', filename)
        # pull out `json`, `yaml` etc. from filename
        base_name, ext = filename.split('.')
        return file_path, ext

    @classmethod
    def load_fixture(cls, fixture_spec, apps, schema_editor):
        original_apps = serializers.python.apps
        serializers.python.apps = apps
        path, fixture_type = cls.fixture_path(*fixture_spec)
        fixture_file = open(path)
        objects = serializers.deserialize(fixture_type,
                                          fixture_file,
                                          ignorenonexistent=True)
        for obj in objects:
            obj.save()
        fixture_file.close()
        serializers.python.apps = original_apps

    @classmethod
    def get_classes(cls, apps, schema_editor):
        db_alias = schema_editor.connection.alias
        for app_name, model_name in cls.model_classes:
            yield apps.get_model(
                app_name, model_name).objects.using(db_alias)

    @classmethod
    def forward(cls, *args):
        for fixture in cls.fixture_files:
            cls.load_fixture(fixture, *args)

    @classmethod
    def reverse(cls, *args):
        for model in cls.get_classes(*args):
            model.all().delete()
