import collections
from random import Random
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from queues.models import Entry, Queue
from queues.tests.models import Widget


def create_model():
    """Just return a random newly created model"""
    return Widget.objects.create()


class QueueTests(TestCase):
    """Tests for the Queue model"""
    def setUp(self):
        super(QueueTests, self).setUp()

        self.item1 = create_model()
        self.item2 = create_model()
        self.queue = Queue.objects.create()

    def test_push_item_create_entry(self):
        queue = self.queue
        item = self.item1
        entry = queue.push(item)

        self.assertEqual(entry.item, item)
        self.assertEqual(entry.order, 0)

    def test_pop_nonempty_pops_first_item(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        item = queue.pop()
        self.assertEqual(item, item1)
        item_content_type = ContentType.objects.get_for_model(item)
        queryset = Entry.objects.filter(
            queue=queue,
            content_type=item_content_type,
            object_id=item.pk,
        )
        self.assertIs(queryset.exists(), False)

    def test_pop_empty_raises_indexerror(self):
        queue = self.queue

        with self.assertRaises(IndexError):
            queue.pop()

    def test_pop_with_n_pops_nth_item(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        item = queue.pop(1)
        self.assertEqual(item, item2)
        item_content_type = ContentType.objects.get_for_model(item)
        queryset = Entry.objects.filter(
            queue=queue,
            content_type=item_content_type,
            object_id=item.pk,
        )
        self.assertIs(queryset.exists(), False)

    def test_pop_with_negative_argument_pops_from_end(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        item = queue.pop(-1)

        self.assertEqual(item, item2)

        item_content_type = ContentType.objects.get_for_model(item)
        queryset = Entry.objects.filter(
            queue=queue,
            content_type=item_content_type,
            object_id=item.pk,
        )
        self.assertIs(queryset.exists(), False)

    def test_count_returns_size_of_queue(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        self.assertEqual(queue.count(), 2)

        queue.pop()
        self.assertEqual(queue.count(), 1)

    def test_clear_empties_queue(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        queue.clear()
        self.assertEqual(queue.count(), 0)

    def test_iter(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        queue_iter = iter(queue)
        self.assertIsInstance(queue_iter, collections.Iterator)

        item = next(queue_iter)
        self.assertEqual(item, item1)

        item = next(queue_iter)
        self.assertEqual(item, item2)

    def test_shuffle_shuffles_the_entries(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2
        item3 = create_model()
        random = Random(55555)
        shuffle = random.shuffle

        queue.push(item1)
        queue.push(item2)
        queue.push(item3)

        with patch('queues.models.Queue.random.shuffle', side_effect=shuffle):
            queue.shuffle()

        self.assertEqual(queue[0], item3)
        self.assertEqual(queue[1], item1)
        self.assertEqual(queue[2], item2)

    def test_indexing(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        self.assertEqual(queue[0], item1)
        self.assertEqual(queue[1], item2)

    def test_negative_indexing(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        self.assertEqual(queue[-1], item2)
        self.assertEqual(queue[-2], item1)

    def test_simple_slicing(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2
        item3 = create_model()

        queue.push(item1)
        queue.push(item2)
        queue.push(item3)

        self.assertEqual(queue[1:], [item2, item3])
        self.assertEqual(queue[:2], [item1, item2])

    def test_contains(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)

        self.assertIs(item1 in queue, True)
        self.assertIs(item2 in queue, False)


class EntryTests(TestCase):
    """Tests for the Entry model"""
    def setUp(self):
        super(EntryTests, self).setUp()

        self.queue = Queue.objects.create()
        self.item1 = create_model()
        self.item2 = create_model()

    def test_adds_order_on_save(self):
        queue = self.queue
        item = self.item1
        entry = Entry.objects.create(queue=queue, item=item)

        self.assertEqual(entry.order, 0)

    def test_adds_biggest_order_plus_one_when_there_are_holes(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        Entry.objects.create(queue=queue, item=item1, order=6)
        Entry.objects.create(queue=queue, item=item2, order=5)

        item3 = create_model()
        entry = Entry.objects.create(queue=queue, item=item3)

        self.assertEqual(entry.order, 7)

    def test_str_method(self):
        queue = self.queue
        item = self.item1
        entry = Entry.objects.create(queue=queue, item=item)
        entry_str = str(entry)

        expected = 'Entry {} in Queue'.format(entry.order)
        self.assertTrue(entry_str.startswith(expected))

    def test_ordered_by_order_despite_insertion_order(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        Entry.objects.create(queue=queue, item=item1, order=6)
        Entry.objects.create(queue=queue, item=item2, order=5)

        queryset = Entry.objects.filter(queue=queue)

        self.assertEqual(queryset[0].order, 5)
        self.assertEqual(queryset[1].order, 6)

    def test_extend_when_empty_adds_each_item_to_queue_in_order(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.extend([item1, item2])

        self.assertEqual(len(queue), 2)
        self.assertEqual(queue[0], item1)
        self.assertEqual(queue[1], item2)

    def test_extend_when_not_empty_adds_each_item_to_queue_in_order(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)

        item3 = create_model()
        item4 = create_model()
        queue.extend([item3, item4])

        self.assertEqual(len(queue), 4)
        self.assertEqual(queue[2], item3)
        self.assertEqual(queue[3], item4)

    def test_remove_when_found_removes_first_matching_item_in_queue(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item2)
        queue.push(item1)

        queue.remove(item1)

        self.assertEqual(len(queue), 2)
        self.assertEqual(queue[0], item2)
        self.assertEqual(queue[1], item1)

    def test_remove_when_not_found_raises_valueerror(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2

        queue.push(item1)
        queue.push(item1)

        with self.assertRaises(ValueError):
            queue.remove(item2)

    def test_reverse_with_no_holes_reverses(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2
        item3 = create_model()

        queue.extend([item1, item2, item3])
        queue.reverse()

        self.assertEqual(queue[:], [item3, item2, item1])

    def test_reverse_with_holes_reverses(self):
        queue = self.queue
        item1 = self.item1
        item2 = self.item2
        item3 = create_model()

        queue.extend([item1, item2, item2, item3, item1])
        queue.pop(2)       # [item1, item2, item3, item1]
        queue.pop(-1)      # [item1, item2, item3]
        queue.push(item2)  # [item1, item2, item3, item2]
        queue.reverse()

        self.assertEqual(queue[:], [item2, item3, item2, item1])

    def test_reverse_with_empty_queue(self):
        queue = self.queue

        queue.reverse()

        self.assertEqual(queue[:], [])
