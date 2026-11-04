import copy
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from demo import load_addresses, verify_pair

HERE = Path(__file__).resolve().parent


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((HERE / 'fixtures/illustrative-addresses.json').read_text(encoding='utf-8'))
        self.csv_text = (HERE / 'fixtures/illustrative-addresses.csv').read_text(encoding='utf-8-sig')

    def test_leading_zero_space_unicode_and_multiline_survive(self):
        records = verify_pair(self.document, self.csv_text)
        self.assertEqual([r['zip'] for r in records], ['00123', 'A1A 1A1'])
        self.assertIn('"Demo"', records[1]['street'])
        self.assertIn('\n', records[1]['sourceFullAddress'])
        self.assertEqual(records[1]['city'], 'Démo')

    def test_numeric_postal_code_is_rejected_not_repaired(self):
        self.document['addresses'][0]['zip'] = 123
        with self.assertRaisesRegex(ValueError, 'string'):
            load_addresses(self.document)

    def test_source_metadata_is_preserved_and_required(self):
        original = copy.deepcopy(self.document)
        self.assertEqual(load_addresses(self.document), self.document['addresses'])
        self.assertEqual(self.document, original)
        self.document['addresses'][0].pop('sourceId')
        with self.assertRaisesRegex(ValueError, 'sourceId'):
            load_addresses(self.document)

    def test_swapped_locality_postcode_pair_is_detected(self):
        self.document['addresses'][0]['zip'] = '99999'
        with self.assertRaisesRegex(ValueError, 'ZIP'):
            verify_pair(self.document, self.csv_text)

    def test_unrelated_source_credit_is_rejected(self):
        self.document['sources'] = []
        with self.assertRaisesRegex(ValueError, 'credit'):
            load_addresses(self.document)

    def test_different_source_record_url_is_detected(self):
        self.document['addresses'][0]['sourceRecordUrl'] = 'https://example.invalid/fixtures/other'
        with self.assertRaisesRegex(ValueError, 'source credit'):
            verify_pair(self.document, self.csv_text)

    def test_missing_csv_row_is_detected(self):
        self.document['addresses'] = self.document['addresses'][:1]
        with self.assertRaisesRegex(ValueError, 'row counts'):
            verify_pair(self.document, self.csv_text)

    def test_truncated_csv_and_postcode_tool_schema_are_rejected(self):
        with self.assertRaises(ValueError):
            verify_pair(self.document, 'Street,City,State,ZIP,Country\nOne,Only\n')
        with self.assertRaisesRegex(ValueError, 'schemaVersion'):
            load_addresses({'tool': 'postcode-generator', 'records': []})

    def test_spreadsheet_guard_only_matches_exported_value(self):
        self.document['addresses'][0]['street'] = '=DEMO'
        rows = list(csv.DictReader(io.StringIO(self.csv_text)))
        rows[0]['Street'] = "'=DEMO"
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        verify_pair(self.document, output.getvalue())
        rows[0]['Street'] = "'Other value"
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, 'Street'):
            verify_pair(self.document, output.getvalue())

    def test_cli_runs_from_path_with_spaces_without_network(self):
        with tempfile.TemporaryDirectory(prefix='address demo ') as directory:
            root = Path(directory)
            (root / 'input.json').write_text(json.dumps(self.document), encoding='utf-8')
            (root / 'input.csv').write_text(self.csv_text, encoding='utf-8-sig')
            result = subprocess.run([sys.executable, str(HERE / 'demo.py'), str(root / 'input.json'), str(root / 'input.csv')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['records'], 2)


if __name__ == '__main__':
    unittest.main()
