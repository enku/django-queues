"""Models for tests"""
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from queues.models import Entry


class Widget(models.Model):
    """Just a random model"""
    category_id = models.PositiveIntegerField(null=True)
    queue = GenericRelation(Entry, related_query_name='queue_entry')
