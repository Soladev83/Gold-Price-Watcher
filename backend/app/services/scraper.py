"""
Gold price scraper for Ethiopian Birr (ETB).
Primary source: livepriceofgold.com/ethiopia-gold-price.html
Fallback source: goldpricez.com/et/gram (24K only)

Both sources derive prices from the international spot price converted
via the live ETB/USD exchange rate — label every record accordingly.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PRIMARY_URL = "https://livepriceofgold.com/ethiopia-gold-price.html"
FALLBACK_URL = "https://goldpricez.com/et/gram"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class GoldPriceSnapshot:
    fetched_at: datetime          # UTC
    price_24k: float              # ETB per gram
    price_22k: Optional[float]
    price_18k: Optional[float]
    source_url: str
    source_label: str = "Reference price (livepriceofgold.com). Not a dealer quote."


def _parse_number(text: str) -> Optional[float]:
    """Strip commas/spaces and convert to float."""
    try:
        return float(text.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Primary scraper — livepriceofgold.com
# ---------------------------------------------------------------------------

def _scrape_primary(html: str) -> Optional[GoldPriceSnapshot]:
    soup = BeautifulSoup(html, "html.parser")

    prices: dict[str, Optional[float]] = {"24K": None, "22K": None, "18K": None}

    # The page has a table with rows like "1 GRAM GOLD 24K | 22,800.39 | ..."
    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True).upper()
        value_text = cells[1].get_text(strip=True)
        for purity in ("24K", "22K", "18K"):
            if purity in label and "GRAM" in label:
                prices[purity] = _parse_number(value_text)

    if prices["24K"] is None:
        logger.warning("Primary scraper: 24K price not found in HTML.")
        return None

    return GoldPriceSnapshot(
        fetched_at=datetime.now(timezone.utc),
        price_24k=prices["24K"],
        price_22k=prices["22K"],
        price_18k=prices["18K"],
        source_url=PRIMARY_URL,
        source_label="Reference price (livepriceofgold.com). Not a dealer quote.",
    )


# ---------------------------------------------------------------------------
# Fallback scraper — goldpricez.com (24K only)
# ---------------------------------------------------------------------------

def _scrape_fallback(html: str) -> Optional[GoldPriceSnapshot]:
    soup = BeautifulSoup(html, "html.parser")

    # The page renders a value like "22,472.26" inside a span/div near "ETB"
    # Try multiple candidate selectors
    candidate_selectors = [
        {"class_": "price"},
        {"class_": "gold-price"},
        {"id": "cPrice"},
    ]
    price_text: Optional[str] = None
    for sel in candidate_selectors:
        tag = soup.find(attrs=sel)
        if tag:
            price_text = tag.get_text(strip=True)
            break

    # Broad fallback: scan all text for "ETB" proximity
    if price_text is None:
        for tag in soup.find_all(string=True):
            text = tag.strip()
            if "ETB" in text:
                # Try extracting number before "ETB"
                parts = text.replace(",", "").split()
                for part in parts:
                    try:
                        val = float(part)
                        if 5_000 < val < 500_000:   # sanity: reasonable ETB/g range
                            price_text = part
                            break
                    except ValueError:
                        continue
            if price_text:
                break

    price = _parse_number(price_text) if price_text else None
    if price is None:
        logger.error("Fallback scraper: could not extract 24K price.")
        return None

    # Derive 22K and 18K from 24K using standard purity ratios
    price_22k = round(price * (22 / 24), 2)
    price_18k = round(price * (18 / 24), 2)

    return GoldPriceSnapshot(
        fetched_at=datetime.now(timezone.utc),
        price_24k=price,
        price_22k=price_22k,
        price_18k=price_18k,
        source_url=FALLBACK_URL,
        source_label=(
            "Reference price (goldpricez.com, 24K only; 22K/18K derived by purity ratio). "
            "Not a dealer quote."
        ),
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def fetch_gold_prices() -> GoldPriceSnapshot:
    """
    Fetch the latest Ethiopian gold prices.
    Tries the primary source first; falls back to goldpricez.com on failure.
    Raises RuntimeError if both sources fail.
    """
    async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        # --- Primary ---
        try:
            resp = await client.get(PRIMARY_URL)
            resp.raise_for_status()
            snapshot = _scrape_primary(resp.text)
            if snapshot:
                logger.info("Fetched gold prices from primary source.")
                return snapshot
            logger.warning("Primary source returned data but parsing failed; trying fallback.")
        except Exception as exc:
            logger.warning("Primary source request failed: %s", exc)

        # --- Fallback ---
        try:
            resp = await client.get(FALLBACK_URL)
            resp.raise_for_status()
            snapshot = _scrape_fallback(resp.text)
            if snapshot:
                logger.info("Fetched gold prices from fallback source.")
                return snapshot
        except Exception as exc:
            logger.error("Fallback source request failed: %s", exc)

    raise RuntimeError(
        "Both gold price sources failed. Check network connectivity or source availability."
    )
