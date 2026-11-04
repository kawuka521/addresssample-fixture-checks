"""Check current AddressSample address exports offline; never validate delivery."""
import csv
import io
import json
import re
import sys
from pathlib import Path

FIELDS = {'Street': 'street', 'City': 'city', 'State': 'state', 'ZIP': 'zip', 'Country': 'country', 'FullAddress': 'sourceFullAddress'}


def load_addresses(document):
    if document.get('schemaVersion') != 1 or not isinstance(document.get('addresses'), list):
        raise ValueError('Expected address export schemaVersion 1 and addresses, not postal-tool records')
    for index, row in enumerate(document['addresses'], 1):
        for field in [*FIELDS.values(), 'countryCode', 'premisesId', 'sourceType', 'sourceVersion', 'sourceId', 'sourceRecordUrl']:
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValueError(f'Row {index}: {field} must be a nonempty string')
        credits = [s for s in document.get('sources', []) if s.get('countryCode') == row['countryCode']]
        if not credits or not all(credits[0].get(k) for k in ['source', 'license', 'licenseUrl']):
            raise ValueError(f'Row {index}: missing country source credit')
    return document['addresses']


def spreadsheet_cell(text):
    # The address exporter guards spreadsheet formula prefixes with an apostrophe.
    return "'" + text if re.match(r'^\s*[=+@-]', text) else text


def verify_pair(document, csv_text):
    addresses = load_addresses(document)
    reader = csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff'), newline=''), strict=True)
    required = {*FIELDS, 'LocationSource', 'License', 'StreetType'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('CSV lacks required address-export columns')
    try:
        rows = list(reader)
    except csv.Error as error:
        raise ValueError(f'Malformed CSV: {error}') from error
    if len(rows) != len(addresses):
        raise ValueError('CSV and JSON row counts differ; export both from the same batch')
    for index, (address, row) in enumerate(zip(addresses, rows), 1):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f'Row {index}: CSV column count mismatch')
        for column, key in FIELDS.items():
            expected = address[key]
            if column == 'State' and address['countryCode'] in {'HK', 'JP', 'KR'} and address.get('addressLanguage'):
                expected = address['stateName']
            if row[column] != spreadsheet_cell(expected):
                raise ValueError(f'Row {index}: {column} differs between CSV and JSON')
        credit = next(s for s in document['sources'] if s['countryCode'] == address['countryCode'])
        if address['sourceRecordUrl'] not in row['LocationSource'] or credit['source'] not in row['LocationSource'] or credit['licenseUrl'] not in row['License']:
            raise ValueError(f'Row {index}: CSV source credit differs from JSON')
    return addresses


def main():
    args = sys.argv[1:] or ['fixtures/illustrative-addresses.json', 'fixtures/illustrative-addresses.csv']
    if len(args) != 2:
        raise ValueError('Usage: python demo.py addresses.json addresses.csv')
    document = json.loads(Path(args[0]).read_text(encoding='utf-8-sig'))
    rows = verify_pair(document, Path(args[1]).read_text(encoding='utf-8-sig'))
    print(json.dumps({'records': len(rows), 'postalCodes': [r['zip'] for r in rows], 'sourceMetadataPreserved': True, 'deliveryVerified': False}, ensure_ascii=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
