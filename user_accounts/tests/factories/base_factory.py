import random


class PrepopulatedModelFactory:
    """Most of the models in user_accounts are loaded from fixtures
    This class creates a factory from an existing populated table.
    """

    def __init__(self, queryset):
        self.queryset = queryset
        self.row_count = None

    def ensure_table_is_populated(self):
        self.objects = list(self.queryset)
        self.row_count = len(self.objects)
        if not self.row_count:
            raise Exception(
                "`{}` table is not yet populated.".format(
                    self.queryset.model.__name__))

    def choice(self):
        self.ensure_table_is_populated()
        return random.choice(self.objects)

    def sample(self, count=None, zero_is_okay=False):
        self.ensure_table_is_populated()
        if not count:
            lower_limit = 0 if zero_is_okay else 1
            count = random.randint(lower_limit, self.row_count)
        return random.sample(self.objects, count)
