from django.db import models, connections


def run_query(query):
    """Takes a raw sql query and returns a list of lists.

    This function used a special `purged` database to protect users
    which connects to a read-only replicate with a special user.
    """
    with connections['purged'].cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
    return result


class Clip(models.Model):
    query = models.TextField(null=False, blank=False)
