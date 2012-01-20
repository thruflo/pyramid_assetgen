#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import dirname, join as join_path
from setuptools import setup, find_packages

def _read(file_name):
    sock = open(file_name)
    text = sock.read()
    sock.close()
    return text
    

def _doc():
    try:
        import pyramid_assetgen
    except ImportError:
        return ''
    else:
        return pyramid_assetgen.__doc__


setup(
    name = 'pyramid_assetgen',
    version = '0.2.2',
    description = 'Integrate Assetgen with the Pyramid framework.',
    long_description = _doc(),
    author = 'James Arthur',
    author_email = 'username: thruflo, domain: gmail.com',
    url = 'http://github.com/thruflo/pyramid_assetgen',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Framework :: Pylons',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    license = _read('UNLICENSE').split('\n')[0],
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'pyramid',
    ],
    tests_require = [
        'WebTest >= 1.3.1',
    ],
)
