class MissingInvitationError(Exception):
    '''Can't find a matching invitation for a user during signup
    '''
    pass


class UnacceptedInviteError(Exception):
    '''The user has not yet accepted this invite
    '''
    pass
