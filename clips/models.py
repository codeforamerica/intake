from django.urls import reverse
from django.db import models, connections


def run_query(query):
    """Takes a raw sql query and returns a list of lists.

    This function used a special `purged` database to protect users
    which connects to a read-only replicate with a special user.
    """
    with connections['purged'].cursor() as cursor:
        cursor.execute(query)
        desc = cursor.description
        headers = [h.name for h in desc]
        result = cursor.fetchall()
        result.insert(0, headers)
    return result


class Clip(models.Model):
    title = models.CharField(max_length=64, null=False, blank=False)
    query = models.TextField(null=False, blank=False)

    @property
    def run(self):
        return run_query(self.query)

    def get_absolute_url(self):
        return reverse('clips-update', kwargs={'pk': self.pk})
