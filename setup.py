import os

from setuptools import setup

README_FILE = os.path.join(os.path.dirname(__file__), 'README.md')

with open(README_FILE, 'r') as fp:
    README = fp.read()


setup(
    name='django-queues',
    version='0.1',
    url='https://github.com/enku/django-queues',
    packages=['queues', 'queues.migrations'],
    include_package_data=True,
    install_requires=['Django>=2.0'],
    license='BSD',
    description='Persistent Queues for Django',
    long_description=README,
    author='Albert Hopkins',
    author_email='marduk@letterboxes.org',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.x',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
