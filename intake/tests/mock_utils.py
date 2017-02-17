
class SimpleMock:
    """This is similar to a unittest.mock.Mock object, except that it only
        instantiates itself with the given kwargs as instance attributes.
        Unlike unittest.mock.Mock it does not allow calls or access to
        attributes that weren't given during instantiation.

        >>> mock_org = SimpleMock(
        ...     name="Example Org",
        ...     county=SimpleMock(name="Yolo"))
        >>> mock_org.name
        'Example Org'
        >>> mock_org.county.name
        'Yolo'
        >>> mock_org.email
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        AttributeError: 'SimpleMock' object has no attribute 'email'
    """

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
