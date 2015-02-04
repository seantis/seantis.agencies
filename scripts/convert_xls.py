# coding=utf-8

import logging
logging.basicConfig()
logger = logging.getLogger('convert_xls')
logger.setLevel(logging.INFO)

import click
import xlrd
import xlwt


# Constants for organisation sheet
hierarchy = (
    u'BAND', u'GEWALT', u'DIREKTION', u'AMT', u'ABTEILUNG', u'GRUPPE'
)
organisation_fields = (
    u'id', u'name', u'node_number'
)
organisation_text_fields = {
    u'BAND': (u'text', ),
    u'GEWALT': (u'periode', u'text'),
    u'DIREKTION': (
        u'adresse1', u'adresse2', u'plz_ort', u'tel', u'fax', u'email', u'www',
        u'text'
    ),
    u'AMT': (
        u'adresse1', u'adresse2', u'plz_ort', u'tel', u'fax', u'email', u'www',
        u'text'
    ),
    u'ABTEILUNG': (
        u'adresse1', u'adresse2', u'plz_ort', u'tel', u'fax', u'email', u'www',
        u'text'
    ),
    u'GRUPPE': (
        u'adresse1', u'adresse2', u'plz_ort', u'tel', u'fax', u'email', u'www',
        u'text'
    )
}

# Constants for person sheet
person_fields = (
    u'id', u'node_number',
    u'band', u'gewalt', u'direktion', u'amt', u'abteilung', u'gruppe',
)
person_text_fields = (
    u'name', u'vorname', u'jahrgang', u'anrede', u'titel', u'adresse',
    u'partei', u'eintritt', u'tel_int', u'tel_ext', u'fax', u'email', u'www',
    u'funktion', u'period', u'begriffe'
)


def parse_input(filename, verbose):
    """Read the input file and store the data in a nested array."""

    workbook = xlrd.open_workbook(filename)
    sheets = dict(((sheet.name, sheet) for sheet in workbook.sheets()))
    assert all((sheet in sheets.keys() for sheet in hierarchy))
    assert u'PERSON' in sheets.keys()

    # Read all organisations
    organisations = {}
    for level in range(len(hierarchy)):
        name = hierarchy[level]
        organisations[name] = get_organisations_in_sheet(level, sheets)

    # Fill in children
    for level in range(len(hierarchy)-1):
        parents = dict((
            (parent[u'id'], parent) for parent
            in organisations[hierarchy[level]]
        ))
        for child in organisations[hierarchy[level+1]]:
            if child[u'parent'] not in parents.keys():
                if verbose:
                    logger.warning(
                        u'Orphaned organisation \'%s\' found in %s' % (
                            child[u'name'], hierarchy[level+1].title()
                        )
                    )
            else:
                children = parents[child[u'parent']][u'children']
                assert child not in children
                children.append(child)

    # Fill in people
    people = get_people(sheets[u'PERSON'])
    for level in range(len(hierarchy)):
        for organisation in organisations[hierarchy[level]]:
            members = [
                person for person in people
                if person[hierarchy[level].lower()] and int(
                    person[hierarchy[level].lower()]
                ) == organisation[u'id']
            ]
            if members:
                organisation[u'people'] = sorted(
                    members, key=lambda x: x[u'node_number']
                )

    return organisations[hierarchy[0]]


def get_organisations_in_sheet(level, sheets):
    """Returns all organisations in one sheet."""
    sheet = sheets[hierarchy[level]]

    # Read all rows
    rows = []
    for row in range(sheet.nrows):
        columns = []
        for column in range(sheet.ncols):
            columns.append(sheet.cell(row, column).value)
        rows.append(columns)

    # Find the indexes to the required fields
    assert len(rows) >= 1
    header = rows[0]
    fields = organisation_fields + organisation_text_fields[hierarchy[level]]
    assert all((field in header for field in fields))
    indexes = dict(
        ((field, header.index(field)) for field in fields)
    )
    indexes[u'parent'] = None
    if level >= 1:
        assert hierarchy[level-1].lower() in header
        indexes[u'parent'] = header.index(hierarchy[level-1].lower())

    # Sort on node_number
    assert header[-1] == u'node_number'
    rows = sorted(rows[1:], key=lambda row: row[-1])

    # Create a list of all organisations
    organisations = []
    for row in rows:
        parent = None
        if indexes[u'parent'] is not None:
            parent = int(row[indexes[u'parent']])
        text_fields = (
            row[indexes[field]] for field
            in organisation_text_fields[hierarchy[level]]
        )

        organisation = dict(
            ((field, row[indexes[field]]) for field in organisation_fields)
        )
        organisation[u'id'] = int(organisation[u'id'])
        organisation[u'name'] = organisation[u'name'].strip()
        organisation[u'text'] = parse_organisation_text(text_fields)
        organisation[u'parent'] = parent
        organisation[u'children'] = []
        organisation[u'people'] = []
        organisations.append(organisation)

    return organisations


def parse_organisation_text(fields):
    """Does some improvement on the organisation text."""
    parsed = []
    for field in fields:
        text = field.strip()
        if not text:
            continue

        if u'http' in text:
            # Fix corrupted links
            assert u'www.' not in text
            assert u'target=_blank' in text
            text = text.replace(u'target=_blank', u'')
            text = text.replace(u'  ', u' ')
            text = text.replace(u' >', u'>')
            text = text.replace(u'href=', u'href="')
            text = text.replace(u'>', u'">')

        elif u'@' in text:
            # Embedd email addresses
            assert u'mailto:' not in text
            assert u'<a' not in text
            assert u' ' not in text
            text = u'<a href="mailto:%s">%s</a>' % (text, text)

        elif u'www.' in text:
            # Embedd addresses
            new_text = u''
            for url in text.split(u' '):
                if u'www.' in url:
                    new_text += u'<a href="%s">%s</a> ' % (url, url)
                else:
                    new_text += url + u' '
            text = new_text.strip()

        text = text.replace('\n', '<br />')
        parsed.append(text)

    return '<br />'.join(parsed)


def get_people(sheet):
    """Returns all people in the given sheet."""

    # Read all rows
    rows = []
    for row in range(sheet.nrows):
        columns = []
        for column in range(sheet.ncols):
            columns.append(sheet.cell(row, column).value)
        rows.append(columns)

    # Find the indexes to the required fields
    assert len(rows) >= 1
    header = rows[0]
    fields = person_fields + person_text_fields
    assert all([field in header for field in fields])
    indexes = dict(
        ((field, header.index(field)) for field in fields)
    )

    # Create a list of all people
    people = []
    for row in rows[1:]:
        person = dict(((field, row[indexes[field]]) for field in fields))

        prefix = u''
        if u'*' in person[u'name']:
            prefix = u'*'
            person['name'] = person['name'].replace('*', '')
        person['prefix'] = prefix

        for field in person_text_fields:
            person[field] = person[field].strip()

        people.append(person)

    return people


def print_organisations(organisations):
    """ Print all organisations."""

    show_people = False

    def r_print_organisations(level, organisation):
        output = '  ' * level + organisation[u'name']
        if organisation[u'people'] and show_people:
            output += ' [%s]' % ', '.join(
                [p[u'vorname']+' '+p[u'name'] for p in organisation[u'people']]
            )
        print output.encode('utf-8')
        for suborganisation in organisation['children']:
            r_print_organisations(level+1, suborganisation)

    for organisation in organisations:
        r_print_organisations(0, organisation)


def export_organizations(organisations, output, verbose):

    def r_export_organizations(sheet, people, organisation):
        index = len(sheet.rows)
        sheet.row(index).write(0, str(organisation[u'uid']))
        sheet.row(index).write(1, ','.join(
            [str(child[u'uid']) for child in organisation[u'children']]
        ))
        sheet.row(index).write(2, organisation[u'name'])
        sheet.row(index).write(3, organisation[u'text'])
        sheet.row(index).write(4, u'')

        for person in organisation[u'people']:
            if not person[u'name'] and not person[u'vorname']:
                if verbose:
                    logger.warning(
                        u'Ignored empty person %i (%s)' % (
                            int(person[u'id']), ' '.join(
                                [person[field] for field
                                 in person_text_fields if person[field]]
                            )
                        )
                    )
                continue

            set_organisation = True
            duplicates = [
                index for index, existing in enumerate(people)
                if existing[u'name'] == person[u'name']
                and existing[u'vorname'] == person[u'vorname']
            ]
            for duplicate in duplicates:
                mergable = all([
                    not people[duplicate][field] or
                    not person[field] or
                    people[duplicate][field] == person[field]
                    for field in person_text_fields
                ])
                if mergable:
                    set_organisation = False
                    for key in person.keys():
                        if not people[duplicate][key] and person[key]:
                            people[duplicate][key] = person[key]
                    people[duplicate][u'organisations'].append(
                        get_organisation_string(organisation, person)
                    )
                    if verbose:
                        logger.info(
                            u'Merge person %i and %i (%s)' % (
                                int(person[u'id']),
                                int(people[duplicate][u'id']),
                                person[u'vorname'] + u' ' + person[u'name']
                            )
                        )
                    break
                else:
                    if verbose:
                        logger.warning(
                            u'Could not merge person %i and %i (%s)' % (
                                int(person[u'id']),
                                int(people[duplicate][u'id']),
                                person[u'vorname'] + u' ' + person[u'name']
                            )
                        )

            if set_organisation:
                person[u'organisations'] = [
                    get_organisation_string(organisation, person)
                ]
                people.append(person)

        for suborganisation in organisation[u'children']:
            r_export_organizations(sheet, people, suborganisation)

    organisations = assign_uids(organisations)

    book = xlwt.Workbook(encoding='utf-8')
    people = []

    sheet_organisations = book.add_sheet(u'Organisationen')
    sheet_organisations.row(0).write(0, u'ID')
    sheet_organisations.row(0).write(1, u'Unterorganisationen')
    sheet_organisations.row(0).write(2, u'Titel')
    sheet_organisations.row(0).write(3, u'Beschreibung')
    sheet_organisations.row(0).write(4, u'Portrait')

    sheet_organisations.row(1).write(0, u'0')
    sheet_organisations.row(1).write(1, u','.join(
        [str(organisation[u'uid']) for organisation in organisations])
    )
    sheet_organisations.row(1).write(2, u'Organisationen')
    sheet_organisations.row(1).write(3, u'')
    sheet_organisations.row(1).write(4, u'')

    for organisation in organisations:
        r_export_organizations(sheet_organisations, people, organisation)

    sheet_people = book.add_sheet(u'Personen')
    sheet_people.row(0).write(0, u'Akademischer Titel')
    sheet_people.row(0).write(1, u'Beruf')
    sheet_people.row(0).write(2, u'Vorname')
    sheet_people.row(0).write(3, u'Nachname')
    sheet_people.row(0).write(4, u'Politische Partei')
    sheet_people.row(0).write(5, u'Jahrgang')
    sheet_people.row(0).write(6, u'E-Mail')
    sheet_people.row(0).write(7, u'Adresse')
    sheet_people.row(0).write(8, u'Telefon')
    sheet_people.row(0).write(9, u'Direktnummer')
    sheet_people.row(0).write(10, u'Anrede')
    sheet_people.row(0).write(11, u'Fax')
    sheet_people.row(0).write(12, u'Website')
    sheet_people.row(0).write(13, u'Stichworte')
    sheet_people.row(0).write(14, u'Bemerkungen')
    sheet_people.row(0).write(15, u'Organisationen')

    people.sort(key=lambda person: person[u'name']+person[u'vorname'])

    for index, person in enumerate(people):
        sheet_people.row(index+1).write(0, person[u'titel'])
        sheet_people.row(index+1).write(1, u'')
        sheet_people.row(index+1).write(2, person[u'vorname'])
        sheet_people.row(index+1).write(3, person[u'name'])
        sheet_people.row(index+1).write(4, person[u'partei'])
        sheet_people.row(index+1).write(5, person[u'jahrgang'])
        sheet_people.row(index+1).write(6, person[u'email'])
        sheet_people.row(index+1).write(7, person[u'adresse'])
        sheet_people.row(index+1).write(8, person[u'tel_ext'])
        sheet_people.row(index+1).write(9, person[u'tel_int'])
        sheet_people.row(index+1).write(10, person[u'anrede'])
        sheet_people.row(index+1).write(11, person[u'fax'])
        sheet_people.row(index+1).write(12, person[u'www'])
        sheet_people.row(index+1).write(13, person[u'begriffe'])
        sheet_people.row(index+1).write(14, u'')
        sheet_people.row(index+1).write(15, u'//'.join(
            person[u'organisations']
        ))

    book.save(output)


def assign_uids(organisations):
    """Adds uids to organisations"""

    def r_assign_uids(index, organisation):
        organisation[u'uid'] = index
        for suborganisation in organisation['children']:
            index = r_assign_uids(index+1, suborganisation)
        return index

    index = 1
    for organisation in organisations:
        index = r_assign_uids(index+1, organisation)

    return organisations


def get_organisation_string(organisation, person):
    assert person in organisation[u'people']

    return u'(%s)(%s)(%s)(%s)(%s)' % (
        organisation[u'uid'],
        person[u'funktion'],
        person[u'eintritt'],
        person[u'prefix'],
        organisation[u'people'].index(person)
    )


@click.command()
@click.option('--verbose/--no-verbose', default=False,
              help='Show more information')
@click.option('--show/--no-show', default=False,
              help='Show organisation structure')
@click.argument('input')
@click.argument('output')
def convert(input, output, show, verbose):
    """Convert a XLS database export to an importable XLS import file."""
    organisations = parse_input(input, verbose)
    if show:
        print_organisations(organisations)
    export_organizations(organisations, output, verbose)


if __name__ == '__main__':
    convert()
