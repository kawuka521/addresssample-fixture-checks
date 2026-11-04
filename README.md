# Check address-test exports without losing postal codes

A small, offline Python example for comparing CSV and JSON downloaded from the **same address batch**. It keeps postal codes as strings, checks that street/locality/region/postal fields agree across formats, and keeps the JSON source metadata intact.

Python 3.10+; standard library only. No package installation, network access, account, API key or database is needed to run the bundled demonstration. Tested locally with Python 3.12.10.

## Run the included example

Open a terminal in this directory:

```sh
python demo.py
python -m unittest discover -s . -v
```

Expected demo output:

```json
{"records": 2, "postalCodes": ["00123", "A1A 1A1"], "sourceMetadataPreserved": true, "deliveryVerified": false}
```

The two bundled records are **invented regression fixtures**, not actual postal data or a download from a third-party database. Their locality/code combinations are deliberately illustrative, not assertions that those codes are assigned there. Source URLs use `example.invalid`; do not try to resolve them or use these fixtures as real destinations. The second record includes a comma, quotes, Unicode and an embedded newline to exercise real CSV parsing.

## Try your own current AddressSample batch

1. Open the [US address tool](https://addresssample.com/en/), choose **Massachusetts**, then open **Batch addresses · direct export**. Choose 20 and select **Generate batch**.
2. Download **both** CSV and JSON before generating another batch or changing filters. Save them locally as `private-exports/addresses.csv` and `private-exports/addresses.json`; create that directory if necessary.
3. Run:

```sh
python demo.py private-exports/addresses.json private-exports/addresses.csv
```

For a Canadian example, use [Canada](https://addresssample.com/en/canada/), choose Ontario and then Toronto, generate 20, and download both formats from that batch. Smaller locality pools can return fewer records than requested; use the actual returned count.

The command exits nonzero on a mismatched checked address field, missing source metadata, unsupported envelope or malformed/truncated CSV. It compares street, city, state/region, ZIP, country and full address, plus the source-credit references; it does not compare profile fields such as names or phone numbers. It prints a count and postal strings on success, and writes nothing to the input files. Do not combine the JSON from one random batch with CSV from another.

## The two export shapes are different

Current **address** exports use a JSON envelope with `schemaVersion: 1`, `sources` and `addresses`. A current sourced address includes `street`, `city`, `state`, `country`, **`zip` as a string**, `premisesId`, `sourceType`, `sourceVersion`, `sourceId`, `sourceRecordUrl` and `sourceFullAddress`. CSV uses `Street`, `City`, `State`, **`ZIP`**, `Country`, `LocationSource`, `License`, `StreetType` and `FullAddress`, plus profile fields.

The separate [postal-code tool](https://addresssample.com/en/postcode-generator/) instead exports `tool`, `generatedAt` and `records`, where each record uses **`postalCode`**, `city`, `region`, `regionCode`, `country` and source credits. That envelope is intentionally rejected by this address demo. A postal sample has no street address, and one reference locality does not enumerate every place sharing that code.

This demo targets current sourced address batches. Old saved records with fictional delivery details may have a different provenance contract and are not supported here. For HK/JP/KR current address writing, the CSV State field can contain the written region name; the verifier follows that exporter behavior.

## Preserve identifiers, not just formatting

`int("00123")` becomes `123`. Converting back with `str()` cannot recover the original length. JSON strings preserve it; Python's `csv.DictReader` also returns ordinary fields as text. Do not opt into automatic numeric conversion. In Excel or another spreadsheet, import ZIP/postal columns as **Text** before opening or transforming the data; CSV quoting alone does not force spreadsheet text types.

Read CSV with a real parser: a comma can occur inside a street, quotes are doubled inside quoted fields, and a full address can span multiple physical lines. Splitting on commas or line breaks corrupts those records. Use `encoding="utf-8-sig"` for the export's optional BOM.

The actual address exporter prefixes spreadsheet-formula-like cells with an apostrophe. The verifier compares against that documented representation; it does not strip every leading apostrophe from arbitrary input. JSON remains the authoritative unchanged string representation for programmatic import.

## Keep the provenance relationship

Keep the original envelope and every row's source identifiers alongside the fixture. `sourceId` / `sourceRecordUrl` identify the contributing source record, `premisesId` is the site's record identifier, and `sourceVersion` identifies its snapshot. `sources[]` carries country-level attribution and license links. CSV includes readable credits but does not carry all those machine-readable source keys; do not discard JSON and claim you can reconstruct its full provenance from CSV.

The checker confirms that two exports agree and that attribution fields are present. It **does not** look up a source URL, verify the database against an independent authority, grant redistribution rights, check postal assignment, or prove deliverability. Two identically incorrect files can still agree. Keep locality/region/postal fields from the same row; do not independently shuffle them. Sourced premises are not fictional locations, and fictional profile names do not make a real source address anonymous test data.

Review the site's [Data sources](https://addresssample.com/en/sources/) and the exact license links inside your own download before sharing data. The current US/CA source-address exports credit OpenStreetMap contributors and link to the ODbL; postal-only datasets have their own credits and should not be relabelled as the same source. See [OpenStreetMap's attribution and license page](https://www.openstreetmap.org/copyright).

## What the tests cover

Leading zeros; spaced Canadian-shaped text; Unicode, quotes, commas and multiline fields; numeric-code rejection; metadata preservation; missing country credits; row mismatch; truncated CSV; postal-tool-envelope rejection; spreadsheet guards; and a CLI run from a path containing spaces. Separate integration checks in the website project exercise current US/CA serializers; real source records and internal evidence are not bundled here.

Reference behavior: AddressSample release asset version `df0d451b5007`, checked 2026-11-03. This is a consumer example, not a promise of a stable API. No API client or live scraper is included.

`private-exports/` is ignored. Keep your downloaded data out of commits; only the two invented regression fixtures are included here.

## License

Code and original illustrative fixtures in this repository are available under the [MIT License](LICENSE), Copyright (c) 2026 kawuka521. Downloaded source data has its own terms and is not included in this repository; retain its original source and license information.

Disclosure: this project was prepared with AI assistance and locally tested. It contains original illustrative fixtures; no third-party address dataset is bundled.
