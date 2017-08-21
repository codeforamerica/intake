def dont_audit_fixture_loading(
        instance, object_json_repr, created, raw, using, update_fields, **kwargs):
    if not raw:
        print(instance, object_json_repr, created, raw, using, update_fields, **kwargs)
        return True
    else:
        return False
