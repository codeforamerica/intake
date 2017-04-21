import random


class PrepopulatedModelFactory:
    """Most of the models in user_accounts are loaded from fixtures
    This class creates a factory from an existing populated table.
    """

    @classmethod
    def get_queryset(cls):
        raise NotImplementedError("override get_queryset in subclasses")

    @classmethod
    def get_table_count(cls):
        count = cls.get_queryset().count()
        if not count:
            raise Exception(
                "`{}` table is not yet populated.".format(
                    cls.get_queryset().model.__name__))
        return count

    @classmethod
    def choice(cls):
        cls.get_table_count()
        return random.choice(set(cls.get_queryset()))

    @classmethod
    def sample(cls, count=None, zero_is_okay=False):
        row_count = cls.get_table_count()
        if not count:
            lower_limit = 0 if zero_is_okay else 1
            count = random.randint(lower_limit, row_count)
        return random.sample(set(cls.get_queryset()), count)
