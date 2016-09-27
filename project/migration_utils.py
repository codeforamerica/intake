import os
from django.core import serializers
from django.forms.models import model_to_dict

upsert_sql = """
INSERT INTO {table_name} ({columns})
VALUES ({values})
ON CONFLICT ({lookup_keys})
DO UPDATE
SET ({update_columns}) = (
EXCLUDED.{update_column},
...
)
"""


class FixtureDataMigration:
    """Loads data from a fixture

    `forward` loads the fixture
    `reverse` will delete all rows of the designated models

    `fixture_specs` - should be a list of tuples:
      ('appname', 'MyModel', 'fixture_file_name.json')

    `relation_id_fields` should be a list of strings
        specifying relational fields that contain ids (in place of objects)
        and which consequently require modification before saving
    """

    fixture_specs = []
    lookup_keys = ['id']  # `pk` is `id` in `model_to_dict` output
    relation_id_fields = []

    @classmethod
    def fixture_path(cls, app_name, filename):
        file_path = os.path.join(app_name, 'fixtures', filename)
        # pull out `json`, `yaml` etc. from filename
        base_name, ext = filename.split('.')
        return file_path, ext

    @classmethod
    def update_existing_attributes(cls, instance, data):
        for attribute, value in data.items():
            if attribute in cls.relation_id_fields:
                pk = data.get(attribute, None)
                setattr(instance, attribute + "_id", pk)
            else:
                setattr(instance, attribute, value)

    @classmethod
    def get_existing_model(cls, data, lookup, qset):
        for instance in qset:
            is_object = True
            for key in lookup:
                if getattr(instance, key, None) != lookup[key]:
                    is_object = False
            if is_object:
                cls.update_existing_attributes(instance, data)
                return instance
        return None

    @classmethod
    def update_or_create_object(cls, deserialized_object, queryset):
        data = model_to_dict(deserialized_object.object)
        lookup = {key: data.pop(key) for key in cls.lookup_keys}
        # hack for the default None value of id in model_to_dict results
        data.pop('id', None)
        existing = cls.get_existing_model(data, lookup, queryset)
        instance = existing or deserialized_object
        instance.save()

    @classmethod
    def load_fixture(cls, fixture_spec, apps, schema_editor):
        app_name, model_name, fixture_file_name = fixture_spec
        original_apps = serializers.python.apps
        serializers.python.apps = apps
        queryset = cls.get_model_class(app_name, model_name,
                                       apps, schema_editor)
        path, fixture_type = cls.fixture_path(app_name, fixture_file_name)
        fixture_file = open(path)
        objects = serializers.deserialize(fixture_type,
                                          fixture_file,
                                          ignorenonexistent=True)
        for obj in objects:
            cls.update_or_create_object(obj, queryset)
        fixture_file.close()
        serializers.python.apps = original_apps

    @classmethod
    def get_model_class(cls, app_name, model_name, apps, schema_editor):
        db_alias = schema_editor.connection.alias
        return apps.get_model(app_name, model_name).objects.using(db_alias)

    @classmethod
    def forward(cls, *args):
        for spec in cls.fixture_specs:
            cls.load_fixture(spec, *args)

    @classmethod
    def reverse(cls, *args):
        for app_name, model_name, fixture_file_name in cls.fixture_specs:
            ModelManager = cls.get_model_class(app_name, model_name, *args)
            ModelManager.all().delete()
