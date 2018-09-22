# Django Queues

Persistent Queues for Django

## About

*django-queues* is a Django app that supports persistent queues using Django's
database backend.  Not that this is **not** a task queue, but the [queue
data type](https://en.wikipedia.org/wiki/Queue_%28abstract_data_type%29).
*django-queues* is primarily intented to act as a queue data type, however
it also exhibits other behaviors of Python sequence types such as arbitrary
item access, simple slicing, popping entries at any place in the queue
(including the end), iteration and shuffling.

A `Queue` is a Django model, and each item in the `Queue` can be Django model
(any Django model, including the `Queue` model itself.  For example:

```python
>>> q = Queue.objects.create()
>>> len(q)
0

>>> for user in User.objects.all()[:3]:
...    q.push(user)
>>> len(q)
3

>>> q.pop()
<User: user1>

>>> q.push(q)
>>> q[-1][0]
<User: user2>

>>> user in q
True

>>> for item in q:
...    print(item)
```


## Installation

Install the package via pip:

```console
$ pip install git+https://github.com/enku/django-queues 
```

Once the package is installed, you then can add the `queues` app to your
`INSTALLED_APPS` and run `manage.py migrate queues` to install the database
schema.  Then in your code you can use the `Queue` model as demonstrated
above.  To import the `Queue` model:

```python
from queues.models import Queue
```

## Feedback

If you have any feedback (bug reports, suggestes, patches) please use the
Project's [github page](https://github.com/enku/django-queues).
