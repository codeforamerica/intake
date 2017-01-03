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
