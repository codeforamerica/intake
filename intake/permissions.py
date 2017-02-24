
class PermissionDefinition:
    """A simple python class for hardcoding permissions
    """

    def __init__(self, codename, name):
        self.codename = codename
        self.app_code = 'intake.' + self.codename
        self.name = name

    def as_tuple(self):
        return (self.app_code, self.name)

    def __call__(self):
        return self.as_tuple()


# apps
CAN_SEE_APP_STATS = PermissionDefinition(
    'view_app_stats', 'Can see detailed aggregate information about apps')
CAN_SEE_APP_DETAILS = PermissionDefinition(
    'view_app_details', 'Can see detail information about individual apps')


# notes
CAN_SEE_FOLLOWUP_NOTES = PermissionDefinition(
    'view_application_note', 'Can read the contents of notes from followups')
