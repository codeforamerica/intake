def dont_audit_fixture_loading(
        instance, object_json_repr, created, raw, using, update_fields, **kwargs):
    return not raw
