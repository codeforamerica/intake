from formation.form_base import Form


class DisplayForm(Form):
    """Used to display a set of fields, not for input
    """

    def __init__(self, *args, validate=True, **kwargs):
        """setting display_only to True means that
        calls to .render() will render display versions
        by default.
        """
        super().__init__(*args, validate=validate, **kwargs)
        self.display_only = True

    def build_field(self, field_class):
        """after Form instantiates a field
        this method tags each field with
        display_only = True, ensuring that they
        will not render as inputs
        """
        field = super().build_field(field_class)
        field.display_only = True
        return field
