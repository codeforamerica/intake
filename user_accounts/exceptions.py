class MissingInvitationError(Exception):
    '''Can't find a matching invitation for a user during signup
    '''
    pass


class UnacceptedInviteError(Exception):
    '''The user has not yet accepted this invite
    '''
    pass


class UndefinedResourceAccessError(Exception):
    '''Someone should not have access to this resource
    '''
    pass


class NoEmailsForOrgError(Exception):
    '''There is no email contact available for this organization
    '''
    pass
