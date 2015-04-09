Seantis Agencies
================

A directory of people for (government) agencies.

Installation
------------

1. Use Plone 4.3 or newer

::

    extends =
        http://dist.plone.org/release/4.3/versions.cfg

2. Add the module to your instance eggs

::

    [instance]
    eggs +=
        seantis.agencies


3. Ensure that the i18n files are compiled by adding

::

    [instance]
    ...
    environment-vars =
        ...
        zope_i18n_compile_mo_files true

4. Install seantis.agencies under add-ons in the control panel

Views
-----

pdf
~~~
Called on a organization or on the site root.

Creates a PDF of the current organization and sub-organizations with portrait
and memberships. Redirects to the  file if it already exists. If called on the
site root, a table of contents is included.

Use *force* (*/pdf?force=1*) to force the creation of the PDF.

pdfexport-agencies
~~~~~~~~~~~~~~~~~~
Called on the site root.

Exports - scheduled at 0:30 am - 1) all organizations and sub-organizations
with memberships to a PDF located at the root, 2) a PDF for each organization.

Use *force* (*/pdfexport-agencies?force=1*) to bypass the scheduler and to
force the creation of the PDFs.


Build Status
------------

.. image:: https://travis-ci.org/seantis/seantis.agencies.png?branch=master
  :target: https://travis-ci.org/seantis/seantis.agencies
  :alt: Build Status

Coverage
--------

.. image:: https://coveralls.io/repos/seantis/seantis.agencies/badge.png?branch=master
  :target: https://coveralls.io/r/seantis/seantis.agencies?branch=master
  :alt: Project Coverage

Latests PyPI Release
--------------------
.. image:: https://pypip.in/v/seantis.agencies/badge.png
  :target: https://crate.io/packages/seantis.agencies
  :alt: Latest PyPI Release

License
-------
seantis.agencies is released under GPLv2
