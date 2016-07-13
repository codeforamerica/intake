from project.jinja2 import namify


class AccessorField:

    def __init__(self, default=""):
        self.default = default
        self.keys = []

    def set_keys(self, *keys):
        self.keys = keys

    def get_value(self, data):
        value = data
        for key in self.keys:
            value = getattr(data, key, self.default)
        return value

    def __call__(self, data):
        return self.get_value(data)


class YesNoRadioField(AccessorField):
    def __init__(self, default="Off"):
        super().__init__(default=default)
        self.YES = "Yes"
        self.NO = "No"
        self.OFF = self.default

    def check_str(self, val):
        if val.strip().lower() == 'yes':
            return self.YES
        elif val.strip().lower() == 'no':
            return self.NO
        return self.OFF

    def coerce_to_yes_no_off(self, val):
        if isinstance(val, str):
            return self.check_str(val)
        if val in [True, 1]:
            return self.YES
        elif val in [False, 0]:
            return self.NO
        return self.OFF

    def __call__(self, data):
        value = self.get_value(data)
        return self.coerce_to_yes_no_off(value)

# class NamifyField(AttributeField):
#     def __call__(self, data):
#         value = self.get_value(data)
#         return namify(value)