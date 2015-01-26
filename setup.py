#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

name = 'seantis.agencies'
description = (
    'A directory of people for (government) agencies.'
)
version = '0.3'

requirements = [
    'Plone>=4.3',
    'plone.api',
    'plone.app.dexterity [grok]',
    'five.grok',
    'xlrd',
    'xlwt',
    'seantis.plonetools',
    'seantis.people>=0.24',
    'kantonzugpdf',
    'svglib'
]


test_requirements = [
    'plone.app.testing',
    'collective.betterbrowser[pyquery]',
    'seantis.plonetools[tests]',
    'mock'
]


def get_long_description():
    readme = open('README.rst').read()
    history = open(os.path.join('docs', 'HISTORY.rst')).read()

    # cut the part before the description to avoid repetition on pypi
    readme = readme[readme.index(description) + len(description):]

    return '\n'.join((readme, history))

setup(
    name=name, version=version, description=description,
    long_description=get_long_description(),
    classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='seantis.agencies plone',
    author='Seantis GmbH',
    author_email='Seantis GmbH',
    url='https://github.com/seantis/seantis.agencies',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages='seantis.agencies'.split('.')[:-1],
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    extras_require=dict(
        tests=test_requirements
    ),
    entry_points="""
    # -*- Entry points: -*-

    [z3c.autoinclude.plugin]
    target = plone
    """
)
