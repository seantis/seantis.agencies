Seantis Agencies
================

A directory of people for (government) agencies.

Views
-----

pdfexport
^^^^^^^^^
Called on a organzation.

Creates a PDF of the current organization and sub-organizations with portrait
and memberships. Redirects to the  file if it already exists.

Use *force* (*/pdfexport?force=1*) to force the creation of the PDF.

pdfexport-agencies
^^^^^^^^^^^^^^^^^^
Called on the site root.

Exports - scheduled at 0:30 am - 1) all organizations and sub-organizations
with memberships to a PDF located at the root, 2) a PDF for each organisation
(calling */pdfexport* for every organization).

Use *force* (*/pdfexport-agencies?run=1&force=1*) to bypass the scheduler and
to force the creation of the PDFs.


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
