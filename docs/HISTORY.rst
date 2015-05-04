
Changelog
---------

0.8.1 (2015-05-04)
~~~~~~~~~~~~~~~~~~

- Change row widths in PDF.
  [msom]

0.8 (2015-05-03)
~~~~~~~~~~~~~~~~

- Add start of membership to PDF.
  [msom]

- Remove more unprocessable tags in organization portrait for PDF generation.
  [msom]

- Only use unrestricted for saving/deleting the PDF file.
  [msom]

- Change row widths in PDF.
  [msom]

- Optimize event handling when renaming organizations.
  [msom]

0.7.1 (2015-04-08)
~~~~~~~~~~~~~~~~~~

- Reduce querying objects in nightly PDF export. Updates #12.


0.7 (2015-03-31)
~~~~~~~~~~~~~~~~

- Make exported fields selectable. Implements #15.
  [msom]

- Display memberships in person detail view at the bottom.
  [msom]

0.6.3 (2015-03-16)
~~~~~~~~~~~~~~~~~~

- Use a more robust way to implement the last upgrade step.
  [msom]

0.6.2 (2015-03-16)
~~~~~~~~~~~~~~~~~~

- Update memberships if the parent folder has changed. Fixes #11
  [msom]

- Improve PDF export: Add a add view, use transaction savepoints, decrease CPU usage. Updates #7
  [msom]

0.6.1 (2015-03-09)
~~~~~~~~~~~~~~~~~~

- Don't support multiple instances for PDF export for now.
  [msom]

0.6 (2015-03-09)
~~~~~~~~~~~~~~~~

- Export the PDFs nightly using the clock server. Implements #7
  [msom]

- Use unicode_collate_sortkey in membership sorting. Fixes #8
  [msom]

0.5.1 (2015-03-02)
~~~~~~~~~~~~~~~~~~

- Show portrait and memberships of root organizations in PDF. Fixes #6.

0.5 (2015-02-26)
~~~~~~~~~~~~~~~~

- Add Option to Organization for how to Display Memberships #5.
  [msom]

- Change column widths of membership tables in PDF.
  [msom]

- Add PDF Export View to Organization #4.
  [msom]

0.4 (2015-02-24)
~~~~~~~~~~~~~~~~

- Limit the visible levels in the table of contents of the PDF.
  [msom]

- Use less page breaks in the PDF.
  [msom]

- Fix displaying memberships with deleted members.
  [msom]

0.3 (2015-02-09)
~~~~~~~~~~~~~~~~

- Use a more uncommon separator in XLS import/export.
  [msom]

- Add data migration script.
  [msom]

- Add tests.
  [msom]

- Update bootstrap and setuptools.
  [msom]

0.2 (2015-01-21)
~~~~~~~~~~~~~~~~

- Change global_allow to True. See:
  https://github.com/seantis/seantis.people/issues/32
  [href]

- Show parent organization in people list #3
  [msom]

- Add PDF export of organizations #2
  [msom]

0.1 (2014-12-04)
~~~~~~~~~~~~~~~~

- Initial release.
  [msom]
