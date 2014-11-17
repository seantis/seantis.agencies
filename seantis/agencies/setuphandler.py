from seantis.plonetools import setuphandlers

indexes = [
    #('example_index', 'FieldIndex'),
]


def add_catalog_indexes(context, logger=None):
    if indexes:
        setuphandlers.add_catalog_indexes(
            'seantis.agencies', indexes, context, logger
        )


def import_indexes(context):
    if indexes:
        setuphandlers.import_indexes(
            'seantis.agencies', indexes, context
        )
