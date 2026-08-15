"""
Daily collector for surveying-related government tenders.

Sources (see README for why NSW isn't included yet):
  - QTenders (Queensland) — public JSON API, no login required
  - AusTender (federal)   — public server-rendered search page, no login required

Run directly: python3 collector.py
Writes results to data/tenders.json (only currently-open tenders, deduped by source+id).
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

KEYWORDS = ["survey"]  # QTenders/AusTender search already matches "surveying", "surveyor", etc.

DATA_FILE = Path(__file__).parent / "data" / "tenders.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return TAG_RE.sub("", text or "").strip()


def fetch_qld(keyword: str) -> list[dict]:
    """Pull open QLD QTenders results for a keyword via its public search API."""
    results = []
    page = 1
    while True:
        resp = requests.post(
            "https://qtenders.hpw.qld.gov.au/api/search/tenders",
            headers=HEADERS,
            json={"keywords": keyword, "page": page, "pageSize": 50},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        tenders = data.get("tenders", [])
        if not tenders:
            break

        for t in tenders:
            if not t.get("isOpen"):
                continue
            results.append(
                {
                    "source": "qld_qtenders",
                    "id": f"qld-{t['id']}",
                    "title": strip_html(t.get("title")),
                    "agency": t.get("issuerName") or t.get("businessName"),
                    "region": ", ".join(t.get("locations") or []) or "Queensland",
                    "opens": t.get("opens"),
                    "closes": t.get("closes"),
                    "status": t.get("tenderStatus"),
                    "summary": strip_html(t.get("details"))[:500],
                    "link": t.get("tenderAccessUrl") or t.get("tenderPreviewUrl"),
                }
            )

        if len(tenders) < 50:
            break
        page += 1

    return results


def fetch_austender(keyword: str) -> list[dict]:
    """Pull open federal AusTender ATM results for a keyword by parsing the public search page."""
    results = []
    resp = requests.get(
        "https://www.tenders.gov.au/atm",
        params={"filter": "published", "orderBy": "", "Number": "", "Keyword": keyword},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for row in soup.select(".boxEQH > .row"):
        title_el = row.select_one("p.lead")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        fields = {}
        for desc in row.select(".list-desc"):
            label_el = desc.select_one("span")
            value_el = desc.select_one(".list-desc-inner")
            if label_el and value_el:
                label = label_el.get_text(strip=True).rstrip(":")
                fields[label] = value_el.get_text(" ", strip=True)

        link_el = row.select_one(".list-desc-inner a[href]")
        atm_id = link_el.get_text(strip=True) if link_el else None
        link = f"https://www.tenders.gov.au{link_el['href']}" if link_el else None

        if not atm_id:
            continue

        results.append(
            {
                "source": "austender",
                "id": f"au-{atm_id}",
                "title": title,
                "agency": fields.get("Agency"),
                "region": "National (Federal)",
                "opens": None,
                "closes": fields.get("Close Date & Time"),
                "status": "Open",
                "summary": fields.get("Category") or "",
                "link": link,
            }
        )

    return results


def collect() -> list[dict]:
    all_results: dict[str, dict] = {}
    for kw in KEYWORDS:
        for tender in fetch_qld(kw) + fetch_austender(kw):
            all_results[tender["id"]] = tender
    return sorted(all_results.values(), key=lambda t: t.get("closes") or "")


def main():
    tenders = collect()

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "count": len(tenders),
                "tenders": tenders,
            },
            indent=2,
        )
    )
    print(f"Found {len(tenders)} open surveying-related tenders. Saved to {DATA_FILE}")


if __name__ == "__main__":
    main()
