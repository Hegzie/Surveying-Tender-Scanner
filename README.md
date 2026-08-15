# Surveying Tender Scanner

Finds open, surveying-related government tenders so you don't have to check each portal manually.

## Sources (v1)

- **QTenders (Queensland)** — public JSON API, works out of the box.
- **AusTender (federal)** — public search page, works out of the box.
- **NSW** — not included yet. NSW's tender site (buy.nsw.gov.au) blocks plain automated requests; it needs either the official NSW eTendering API (free developer signup at api.nsw.gov.au) or browser automation. Skipped for v1 by choice — revisit if NSW coverage becomes a priority.

## Run it

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python collector.py
```

Results are written to `data/tenders.json` — only currently-open tenders, deduped by source + tender ID.

## Next steps (not built yet)

- A dashboard to view results without opening the JSON file
- Daily automatic scheduling (so this runs without a computer needing to be on)
- Optional: add NSW back in via the official API
