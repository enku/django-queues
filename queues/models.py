"""Models for django queues

The main model here is the `Queue` models. Queues work much the way that
you would expect of this data type, except they are Django models and
therefore persistent. Also they (can only) contain other Django models.
"""
from random import Random
from typing import Iterator

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction


class Queue(models.Model):
    """A Queue/Deque with a model backing

    A `Queue` can be thought of as a container for other (Django)
    models. These models can be pushed into and popped out of the
    `Queue`. A `Queue` can contain any Django model, including other
    Queues. This `Queue` has many, but not all, the properties of Python
    sequences.

    Typical use of the `Queue` is thus::

        >>> q = Queue.objects.create()
        >>> len(q)
        0

        >>> q.push(cat)
        >>> q.push(dog)
        >>> len(q)
        2
        >>> cat = q.pop()
        >>> dog = q.pop()

    Queue items can also be shuffled::

        >>> q.shuffle()


    To clear the `Queue` use the `.clear()` method::

        >>> q.clear()
        >>> len(q)
        0

    Queues are double-ended.  So you can pop it from the back::

        >>> q = Queue.objects.create()
        >>> q.push(cat)
        >>> q.push(dog)
        >>> q.pop(-1)  # -> dog

    The `Queue` supports some sequence-like behavior:

        >>> q.push(cat)
        >>> cat in q
        True

        >>> q[0] == cat
        True

        >>> for pet in q:
        ...    print(pet)
    """
    objects = models.Manager()
    random = Random()

    def push(self, item: models.Model) -> 'Entry':
        """Push an `item` into the queue"""
        entry = Entry.objects.create(queue=self, item=item)

        return entry

    def pop(self, index: int = 0) -> models.Model:
        """Pop the entry at `index` (0-based) from the queue

        return the item
        """
        if index >= 0:
            queryset = self.entries.all()
        else:
            queryset = self.entries.order_by('-order')
            index = -index - 1

        entry = queryset[index]
        item = entry.item

        entry.delete()

        return item

    def count(self) -> int:
        """Return the number of entries in the queue"""
        return self.entries.count()

    def shuffle(self) -> None:
        """Shuffle the entries in the queue"""
        queryset = self.entries.select_for_update()
        orders = list(queryset.values_list('order', flat=True))

        self.random.shuffle(orders)

        with transaction.atomic():
            queryset.update(order=None)
            for entry, order in zip(queryset, orders):
                entry.order = order
                entry.save()

    def clear(self) -> None:
        """Remove all entries from the queue"""
        self.entries.all().delete()

    def __iter__(self) -> Iterator:
        return iter(i.item for i in self.entries.all())

    def __getitem__(self, index: int) -> models.Model:
        if isinstance(index, slice):
            return [i.item for i in self.entries.all()[index]]

        if index >= 0:
            queryset = self.entries.all()
        else:
            queryset = self.entries.order_by('-order')
            index = -index - 1

        return queryset[index].item

    def __contains__(self, item: models.Model) -> bool:
        """Return `True` if the instance contains `item`"""
        content_type = ContentType.objects.get_for_model(item)
        object_id = item.pk
        queryset = self.entries.filter(
            content_type=content_type,
            object_id=object_id
        )

        return queryset.exists()

    __len__ = count


class Entry(models.Model):
    """An entry in a Queue"""
    queue = models.ForeignKey(
        Queue,
        on_delete=models.CASCADE,
        related_name='entries'
    )

    # The `content_type`, `object_id`, and `item` fields refer to the
    # actual "item" (model) that this entry refers to.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey()

    # The sequential order that this entry has in the Queue. Note that
    # because we can pop() from anywhere in the queue, holes in the
    # order may exist. For example:
    #
    # >>> [i.order for i in q.entries.all()]
    # [0, 1, 2]
    # >>> q.pop(1)
    # <User: user2>
    # >>> [i.order for i in q.entries.all()]
    # [0, 2]
    # >>> q.push(user2)
    # <Entry: Entry 3 in Queue object (1)>
    # >>> [i.order for i in q.entries.all()]
    # [0, 2, 3]
    #
    # Also because we can `.shuffle()` the queue, the order that the
    # `Entry` was inserted in the database may not match up with the
    # `.order` field.
    #
    # >>> q.shuffle()
    # [i.order for i in q.entries.order_by('pk')]
    # [2, 3, 0]
    #
    # However this model's default `ordering` is on `order` so the
    # default queryset will return them ordered by `order`.::
    #
    # >>> [i.order for i in q.entries.all()]
    # [0, 2, 3]
    #
    # TODO: remove null=True when Django supports DEFERRED INITIALLY on
    # constraint indices
    order = models.PositiveIntegerField(null=True)

    objects = models.Manager()

    class Meta:
        unique_together = [('queue', 'order')]
        ordering = ('queue', 'order')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None) -> None:
        """Save the current instance."""

        cls = type(self)
        queryset = (
            cls.objects.select_for_update()
            .filter(queue=self.queue)
            .order_by('-order')
        )

        if self.order is None:
            try:
                last_entry = queryset[0]
            except IndexError:
                last_order = -1
            else:
                last_order = last_entry.order

            self.order = last_order + 1

        super(Entry, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def __str__(self) -> str:
        order = self.order
        queue = self.queue

        return f'Entry {order} in {queue}'
