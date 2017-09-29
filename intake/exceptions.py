class JinjaNotInitializedError(Exception):
    pass


class DuplicateTemplateError(Exception):
    pass


class FrontAPIError(Exception):
    pass


class UserCannotBeNoneError(Exception):
    """Raise this if a task is receiving None but needs a user id
    """
    pass


class NoCountiesInSessionError(Exception):
    pass


class NoApplicantInSessionError(Exception):
    pass


class NoFormSpecFoundError(Exception):
    pass


class MissingFillablePDFError(Exception):
    pass


class MultiplePrebuiltPDFsError(Exception):
    pass


class MailgunAPIError(Exception):
    pass
