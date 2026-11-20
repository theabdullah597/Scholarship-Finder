"""Normalizer for untrusted scraped opportunity data, country mapping, and URL canonicalization."""

import html
import re
from datetime import UTC
from decimal import Decimal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup

from app.models.opportunity import FundingType, OpportunityKind
from app.services.ingestion.base import RawOpportunity

# Strips tracking query params to produce clean canonical URLs
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "source",
}

# Country name to ISO 3166-1 alpha-2 mapping
COUNTRY_MAP = {
    "germany": "DE",
    "deutschland": "DE",
    "united states": "US",
    "usa": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "britain": "GB",
    "england": "GB",
    "canada": "CA",
    "france": "FR",
    "switzerland": "CH",
    "japan": "JP",
    "australia": "AU",
    "sweden": "SE",
    "netherlands": "NL",
    "singapore": "SG",
    "south korea": "KR",
    "korea": "KR",
    "saudi arabia": "SA",
    "kenya": "KE",
    "italy": "IT",
    "spain": "ES",
    "ireland": "IE",
    "new zealand": "NZ",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",
    "austria": "AT",
    "belgium": "BE",
}


def sanitize_text(raw_text: str | None) -> str:
    """Sanitize untrusted text: strip script/style tags, HTML tags, and unescape entities."""
    if not raw_text:
        return ""

    # Parse with BeautifulSoup to strip HTML tags safely
    soup = BeautifulSoup(raw_text, "html.parser")
    for script_or_style in soup(["script", "style", "iframe", "object", "embed"]):
        script_or_style.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = html.unescape(text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_canonical_url(url: str) -> str:
    """Normalize and clean URL by removing marketing tracking parameters, fragments, and trailing slashes."""
    if not url:
        return ""

    parsed = urlparse(url.strip())
    # Filter query parameters
    query_params = parse_qsl(parsed.query)
    clean_params = [(k, v) for k, v in query_params if k.lower() not in TRACKING_PARAMS]

    # Normalize path (remove trailing slash except root)
    clean_path = parsed.path.rstrip("/") if len(parsed.path) > 1 else parsed.path

    clean_url = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        clean_path,
        parsed.params,
        urlencode(clean_params),
        "",  # strip fragment
    ))
    return clean_url


def normalize_country(country_raw: str | None, text_context: str = "") -> str:
    """Determine 2-letter ISO country code from explicit value or text context."""
    if country_raw and len(country_raw.strip()) == 2:
        return country_raw.strip().upper()

    search_pool = f"{country_raw or ''} {text_context}".lower()
    for name, code in COUNTRY_MAP.items():
        if re.search(rf"\b{name}\b", search_pool):
            return code

    return "US"  # Default fallback ISO code


def classify_kind(title: str, description: str, explicit_kind: str | None = None) -> str:
    """Classify opportunity kind based on explicit declaration or text heuristics."""
    if explicit_kind and explicit_kind.lower() in [k.value for k in OpportunityKind]:
        return explicit_kind.lower()

    combined = f"{title} {description}".lower()
    if any(k in combined for k in ["internship", "intern", "praktikum"]):
        return OpportunityKind.INTERNSHIP.value
    if any(k in combined for k in ["fellowship", "fellow", "postdoctoral"]):
        return OpportunityKind.FELLOWSHIP.value
    if any(k in combined for k in ["grant", "funding award", "mobility grant"]):
        return OpportunityKind.GRANT.value

    return OpportunityKind.SCHOLARSHIP.value


def classify_funding_type(description: str, explicit_type: str | None = None) -> str:
    """Classify funding type (fully_funded, partially_funded, unfunded, other)."""
    if explicit_type and explicit_type.lower() in [f.value for f in FundingType]:
        return explicit_type.lower()

    combined = description.lower()
    if any(phrase in combined for phrase in ["fully funded", "full tuition", "full scholarship", "100% tuition"]):
        return FundingType.FULLY_FUNDED.value
    if any(phrase in combined for phrase in ["partial", "tuition waiver", "partial funding", "stipend only"]):
        return FundingType.PARTIALLY_FUNDED.value
    if any(phrase in combined for phrase in ["unpaid", "unfunded", "self-funded"]):
        return FundingType.UNFUNDED.value

    return FundingType.PARTIALLY_FUNDED.value


def normalize_raw_opportunity(raw: RawOpportunity) -> dict:
    """Transform and sanitize a raw opportunity into a clean dictionary ready for insertion."""
    clean_title = sanitize_text(raw.title)
    clean_org = sanitize_text(raw.organization) or "International Academic Institution"
    clean_desc = sanitize_text(raw.description)

    # URL normalization
    src_url = raw.source_url.strip()
    canon_url = normalize_canonical_url(raw.canonical_url or src_url)

    # Country & classification
    country_iso = normalize_country(raw.country, f"{clean_title} {clean_desc}")
    kind_val = classify_kind(clean_title, clean_desc, raw.kind)
    funding_val = classify_funding_type(clean_desc, raw.funding_type)

    # Clean fields list
    cleaned_fields = [sanitize_text(f) for f in raw.fields if f and sanitize_text(f)]
    if not cleaned_fields:
        cleaned_fields = ["General Academic Studies"]

    deadline_val = raw.deadline
    if deadline_val and deadline_val.tzinfo is None:
        deadline_val = deadline_val.replace(tzinfo=UTC)

    stipend_min = Decimal(str(raw.stipend_amount_min)) if raw.stipend_amount_min is not None else None
    stipend_max = Decimal(str(raw.stipend_amount_max)) if raw.stipend_amount_max is not None else None

    return {
        "title": clean_title,
        "organization": clean_org,
        "description": clean_desc,
        "country": country_iso,
        "kind": kind_val,
        "funding_type": funding_val,
        "fields": cleaned_fields,
        "source_url": src_url,
        "canonical_url": canon_url,
        "stipend_amount_min": stipend_min,
        "stipend_amount_max": stipend_max,
        "stipend_currency": raw.stipend_currency.upper() if raw.stipend_currency else None,
        "deadline": deadline_val,
    }

