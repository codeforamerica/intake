from django.core.exceptions import ValidationError
from formation.render_base import Renderable


class Unset:
    """A class that allows us to differentiate between None (or null)
        and a value that has not been set.
    """

    def __bool__(self):
        return False

UNSET = Unset()

DEFAULT_CONTEXT_KEY = "no_context"


class BindParseValidate(Renderable):
    """Performs the essential tasks of any form or form field.
    If given raw input data as a dict or MultiValueDict, it
    will parse and validate the data, storing any parsed data
    and any errors that arose.

    This class is intended as a parent class for both
    Form and Field classes
    """
    parent = None
    validators = []
    # context_key is used for scoping errors
    context_key = DEFAULT_CONTEXT_KEY

    def __init__(self, data=UNSET, initial=None, prefix=None,
                 skip_validation_parse_only=False):
        """`raw_input_data` is expected to be a `dict` or `MultiValueDict`
        By default it is `UNSET`.
        """
        super().__init__()
        self.bind(data)
        self.parsed_data = UNSET
        self.errors = {}
        self.warnings = {}
        self.initial_data = initial
        self.skip_validation_parse_only = skip_validation_parse_only
        if prefix:
            self.context_key = prefix + self.context_key

    def preprocess_raw_input_data(self, data):
        return data

    def bind(self, data):
        """Sets or overwrites the raw input for this object
        """
        self.raw_input_data = self.preprocess_raw_input_data(data)

    def is_bound(self):
        """Checks whether or not any raw_input_data was passed to
        instantiate this field. If `self.is_bound() returns True,
        then this object should be able to
        Returns True if any raw input data was passed.
        Returns False if no raw input data was given.
        """
        return self.raw_input_data is not UNSET

    def is_valid(self):
        """returns True if self.errors is UNSET
        False if there are errors.
        """
        if not self.is_bound():
            raise NotImplementedError(
                str(
                    "There is no defined behavior for checking validity of an "
                    "unbound form.\nPlease instantiate this class or call "
                    "`.bind()` with input data before checking validity."
                ))
        if self.parsed_data is UNSET:
            self.parse_and_validate(self.raw_input_data)
        return not bool(self.errors)

    def parse_and_validate(self, raw_data):
        self.parsed_data = self.parse(raw_data)
        if not self.skip_validation_parse_only:
            self.validate()

    def parse(self, raw_data):
        """The default parsing operation does
        nothing and assumes all the raw data is fine.
        In child classes, this method should be responsible for extracting
        data from the raw data and converting it to the appropriate Python
        types
        """
        return raw_data

    def _messages_att_key(self, message_type):
        """defaults to errors
        """
        if 'warning' in message_type:
            att_key = 'warnings'
        else:
            att_key = 'errors'
        return att_key

    def _get_messages_att(self, message_type):
        key = self._messages_att_key(message_type)
        return getattr(self, key)

    def _add_message(self, message_type, message, key=None):
        """Adds warnings or errors based on the message_type
        """
        key = key or self.context_key
        # pull from the fields
        scoped_message_list = self._get_messages_list(message_type, key)
        # don't add the error/warning message if it's already there
        if message not in scoped_message_list:
            scoped_message_list.append(message)
            messages_dict = {key: scoped_message_list}
            # set the error on the fields
            self._get_messages_att(message_type).update(messages_dict)

    def _get_messages_list(self, message_type, key=None, serialized=False):
        """gets warnings/errors, possibly scoped by a key
        """
        key = key or self.context_key
        # pull from fields
        messages_dict = self._get_messages_att(message_type)
        messages_list = messages_dict.get(key, [])
        if serialized:
            return [str(message) for message in messages_list]
        return messages_list

    def add_error(self, error_message, key=None):
        """Adds an error to this object's error dictionary
        If no key is given, it uses this object's default context key.
        """
        self._add_message('error', error_message, key)

    def add_warning(self, warning_message, key=None):
        """Adds a warning to this object's warning dictionary
        If no key is given, it uses this object's default context key.
        """
        self._add_message('warning', warning_message, key)

    def add_error_list(self, error_messages, key=None):
        """Adds a list of error messages to this object's error dictionary
        """
        for message in error_messages:
            self.add_error(message, key)

    def get_errors_list(self, key=None, serialized=False):
        """Returns a list of error messages, scoped by `key`.
        If no key is given, it will return messages based on
        this objects `.context_key`
        """
        return self._get_messages_list(
            'errors', key=key, serialized=serialized)

    def get_warnings_list(self, key=None, serialized=False):
        """Returns a list of warning messages, scoped by `key`.
        If no key is given, it will return messages based on
        this objects `.context_key`
        """
        return self._get_messages_list(
            'warnings', key=key, serialized=serialized)

    def get_serialized_errors(self):
        return {
            key: self.get_errors_list(key=key, serialized=True)
            for key in self.errors}

    def handle_django_validation_error(self, error):
        """Django's ValidationError can include lists of errors,
        dicts of errors or just have a simple error message.
        This method is responsible for pulling error messages out of
        Django ValidationError objects and selecting the right way to
        add the error messages to this object's own error dictionary
        """
        if hasattr(error, 'error_dict'):
            for key, message in error.message_dict.items():
                if isinstance(message, list):
                    self.add_error_list(message, key)
                else:
                    self.add_error(message, key)
        elif hasattr(error, 'error_list'):
            self.add_error_list(error.messages)
        elif hasattr(error, 'message'):
            self.add_error(error.message)
        else:
            self.add_error(error)

    def validate(self):
        """Iterates over self.validators, calling each with self.parsed_data
        If the validator has a `set_context` attribute, call `set_context`
        on the validator with this object as the only argument before
        calling the validator directly.
        """
        for validator in self.validators:
            if hasattr(validator, 'set_context'):
                validator.set_context(self)
            try:
                validator(self.parsed_data)
            except ValidationError as error:
                self.handle_django_validation_error(error)

    @property
    def data(self):
        """This mimicks django's Form api
        """
        return self.raw_input_data

    def __repr__(self):
        template = "{klass}(bound={bound})"
        return template.format(
            klass=self.__class__.__name__,
            bound=self.is_bound()
        )

    def __str__(self):
        return self.render()
