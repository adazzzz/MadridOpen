#!/usr/bin/env python3
"""Fetch Madrid Open match + training data and save as local JSON snapshot."""

from __future__ import annotations

import datetime as dt
import html
import io
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MATCHES_URL = "https://api.wtatennis.com/tennis/tournaments/1038/2026/matches"
TRAINING_URL_TEMPLATE = "https://practice.tmstennis.com/api/iframe?runid=702&public=1&day={day}&mode=0"
PLAYERS_URL = "https://mutuamadridopen.com/jugadores-2026/"
RESULTS_SHELL_URL = "https://mutuamadridopen.com/results/"
RESULTS_BASE_URL = "https://mutuamadridopen.com/results/php/"
ATP_SCHEDULES_URL = "https://mutuamadridopen.com/results/php/?type=schedules"
ATP_DRAWS_URL = "https://mutuamadridopen.com/results/php/?type=draws"
WTA_SCHEDULE_URL = "https://wta-webapi-prod-apimanagement.azure-api.net/atpjoint-api/v1/Scores/Schedule?eventId=1038&eventYear=2026"
WTA_SCHEDULE_API_KEY = "bcba38b89aff4f8392c412118dcefc42"
WTA_RESULTS_INFO_URL = "https://wta-webapi-prod-apimanagement.azure-api.net/api/v1/vw_Match_Infos/2026/1038"
WTA_RESULTS_INFO_API_KEY = "478665fe974f430b9e6418c6a290a136"
WTA_EVENT_DRAWS_URL = "https://wta-webapi-prod-apimanagement.azure-api.net/api/v1/VwEventDrawxmls/2026/1038"
ATP_OFFICIAL_RANKINGS_URL_TEMPLATE = (
    "https://www.atptour.com/en/rankings/singles"
    "?DateWeek=Current+Week&RankRange={rank_range}&Region=all&SortAscending=True&SortField=LastName"
)
ATP_OFFICIAL_DOUBLES_RANKINGS_URL_TEMPLATE = (
    "https://www.atptour.com/en/rankings/doubles"
    "?DateWeek=Current+Week&RankRange={rank_range}&Region=all&SortAscending=True&SortField=LastName"
)
ATP_OFFICIAL_SINGLES_RANKINGS_REPORT_URL = "https://www.protennislive.com/posting/ramr/singles_entry_numerical.pdf"
ATP_OFFICIAL_DOUBLES_RANKINGS_REPORT_URL = "https://www.protennislive.com/posting/ramr/doubles_numerical_entry.pdf"
ATP_PLAYER_PROFILE_URL_TEMPLATE = "https://www.atptour.com/en/players/-/{atp_player_id}/overview"
ATP_OFFICIAL_RANK_RANGE_VALUES = [
    "1-100",
    "100-200",
    "200-300",
    "300-400",
    "400-500",
    "500-600",
    "600-700",
    "700-800",
    "800-900",
    "900-1000",
    "1000-1100",
    "1100-1200",
    "1200-1300",
    "1300-1400",
    "1400-1500",
    "1500+",
]
WTA_OFFICIAL_RANKINGS_URL = "https://www.wtatennis.com/rankings/singles/"
WTA_OFFICIAL_DOUBLES_URL = "https://www.wtatennis.com/rankings/doubles"
ATP_FALLBACK_BEARER_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6IjhFRkIzQUJENkRGNjE4NzdFRDM0RDJDRkI4ODgyNTAxRjIwNjNGQURSUzI1NiIsInR5cCI6ImF0K2p3dCIsIng1dCI6Imp2czZ2VzMyR0hmdE5OTFB1SWdsQWZJR1A2MCJ9."
    "eyJuYmYiOjE3NzAxNDI3NTAsImV4cCI6MTc4ODI4Njc1MCwiaXNzIjoiaHR0cDovL2F1dGgucHJvdGVubmlzbGl2ZS5jb20iLCJhdWQiOiJEYXRhQXBpIiwiY2xpZW50X2lkIjoiTWFkcmlkMTUzNlRvdXJuYW1lbnRUb2tlbkNsaWVudDIwMjYiLCJUb3VybmFtZW50SUQiOiIxNTM2IiwiVG91cm5hbWVudFllYXIiOiIyMDI2IiwianRpIjoiNkE3OTM4M0YxQUU0M0UwRDZCMTczRjY3MzcxRDQyRkYiLCJpYXQiOjE3NzAxNDI3NTAsInNjb3BlIjpbIkRhdGFBcGkuUmVhZCIsIkRhdGFBcGkuVG91cm5hbWVudFRva2VuIl19."
    "VnhsdsaosBn8sRQkC4w3M3s41R7lUmUlTS1dWY4I5-fNemrLC_hIk46ySgTUZSw0EsRaMPmXzu-AOjU76N2UGSL8gCSaZexxbr3H5E0S6BeCK3a4yinP9QheE7j_wD-b-2XmMjruMpFxUWgSiqGx0lndFjwkmamrkJ-0kMe3LV2IBaYaMV8u8IVnczUOF3xv3CE7QBmbeNo5UIQasxbG5qmqsfbBTbAE2gGNnlkeuxFQ1YJ_-RGQMYTh0TjSXf6wVSxDgcSTVIP1fyxfsbwJ-qDm9sG6YAk7I1HPrjaQ4GrmW5yghDOxVHEHmM_bwfGy6JngDSQvDEf-Rt-fZzmwRWXon-HViuqV5k61VRsCEJMgnLYwaY2pa11CehWzovU9B9osVhW5Q8NuoOF_1tNsFwJAB6FeUEi5GcLERLAnj2_wp3K89_3iQc5xTHh45etbgs_W0BeEEvZ5jcAKdf0O91xMTINHbnbV-Db8PHv0xiS6fkHb67LrOb6XebfNRbN3jmsMfPejcZEJotZBNl_hGlsMPCa4sqnos8JhE92mXbk-1iOSWcLQvoyR-GO4LjmCb6JWwXqds0qJVv6hy5A16bumwLC5OBThBFlCGoQv3_XnZs3IMlICRUKJUl4OSoOUmDMID2Sw-fzuY4xWp5rXPowjn_fM_HFHhBfcaGHMyxY"
)
ATP_PLAYER_ID_OVERRIDES = {
    "kjr-nicolai-budkov": "B0U4",
    "vallejo-daniel": "V0DP",
    "doumbia-sadio": "D917",
    "nys-hugo": "N670",
    "reboul-fabien": "RE45",
    "roger-vasselin-edouard": "R613",
}
ATP_RANKING_OVERRIDES_BY_ID = {
    "CD85": 94,
}
WTA_PLAYER_ID_OVERRIDES = {
    "detiuc-anastasia": "323849",
    "errani-sara": "310761",
    "gauff-cori": "328560",
    "kato-miyu": "317612",
    "kichenok-nadiia": "314704",
    "kozyreva-mariia": "325632",
    "melichar-nicole": "316713",
    "mladenovic-kristina": "315616",
    "ninomiya-makoto": "317820",
    "piter-katarzyna": "313806",
    "siskova-anna": "324995",
    "zvonareva-vera": "260142",
    "q-wen-zheng": "328120",
    "qinwen-zheng": "328120",
}

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
SMALL_RE = re.compile(r"<small[^>]*>(.*?)</small>", flags=re.S)
TRAINING_BLOCK_RE = re.compile(r'<div class="(?:mb-4|mt-4)"[^>]*>(.*?)</div>', flags=re.S)
PLAYER_RANKING_DATE_RE = re.compile(r"Ranking a\s*([0-9]{2}/[0-9]{2}/[0-9]{4})", flags=re.I)
PLAYER_TABLE_RE = re.compile(r'<table[^>]*aria-label="[^"]*\b(ATP|WTA)\b[^"]*"[^>]*>(.*?)</table>', flags=re.I | re.S)
TABLE_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", flags=re.I | re.S)
TABLE_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", flags=re.I | re.S)
PLAYER_NAME_PREFIX_RE = re.compile(r"^(?:\([^)]*\)\s*)+")
PLAYER_NAME_PREFIX_TOKEN_RE = re.compile(r"^\(([^)]*)\)\s*")
RESULTS_INDEX_BUNDLE_RE = re.compile(r'<script[^>]+src="(/results/assets/index-[^"]+\.js)"')
RESULTS_VIEW_BUNDLE_RE = re.compile(r"ResultsView-[a-f0-9]+\.js")
ATP_TOKEN_RE = re.compile(r'token:"([^"]+)"')
ISO_CLOCK_RE = re.compile(r"^(\d{2}):(\d{2})(?::(\d{2}))?([+-]\d{2}):?(\d{2})$")
MIDNIGHT_TIME_RE = re.compile(r"T00:00(?::00)?(?:[+-]\d{2}:?\d{2})?$")
ROLE_LABELS = {"coach", "look", "hitting", "practice"}
RANK_NUMBER_RE = re.compile(r"(\d{1,4})")
ATP_RANKING_ABBR_ROW_RE = re.compile(
    r"(?<!\d)"
    r"(?P<rank>\d{1,4})\s+"
    r"(?P<movement>[+-]?\d+|-)\s+"
    r"(?P<abbr>[A-Z]\.\s+[A-Za-zÀ-ÖØ-öø-ÿ'`.-]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ'`.-]+){0,3})\s+"
    r"(?P<points>\d{1,5})\s+"
    r"(?:\d+|-)"
)
ATP_PLAYER_LINK_RE = re.compile(
    r'href="[^"]*/players/[^"/]+/(?P<id>[a-z0-9]{4})(?:/[^"]*)?"[^>]*>(?P<name>.*?)</a>',
    flags=re.I | re.S,
)
ATP_RANKING_REPORT_ROW_RE = re.compile(
    r"^\s*"
    r"(?P<rank>\d{1,4})(?:\s+T)?\s+"
    r"(?P<last>[A-Za-zÀ-ÖØ-öø-ÿ'` .-]+?),\s+"
    r"(?P<first>[A-Za-zÀ-ÖØ-öø-ÿ'` .-]+?)"
    r"(?:\s+\((?P<country>[A-Z]{3})\))?\s+"
    r"(?P<points>\d{1,6})\b",
    flags=re.M,
)
ATP_PROFILE_RANK_STAT_RE = re.compile(
    r'<div[^>]*class="[^"]*\bstat\b[^"]*"[^>]*>\s*'
    r'(?P<rank>\d{1,4})\s*'
    r'<span[^>]*class="[^"]*\bstat-label\b[^"]*"[^>]*>\s*Rank\s*</span>',
    flags=re.I | re.S,
)
ATP_PROFILE_SINGLES_JSON_RANK_RE = re.compile(
    r'(?i)"(?:singlesRank|singlesRanking|currentSinglesRank|currentSinglesRanking)"\s*:\s*"?(\d{1,4})"?'
)
ATP_PROFILE_DOUBLES_JSON_RANK_RE = re.compile(
    r'(?i)"(?:doublesRank|doublesRanking|currentDoublesRank|currentDoublesRanking)"\s*:\s*"?(\d{1,4})"?'
)
WTA_RANKING_ROW_RE = re.compile(
    r"(?<!\d)"
    r"(?P<rank>\d{1,4})\s+"
    r"(?:-|\+?\d+|-?\d+)\s+"
    r"(?P<name>[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'` .-]{2,80}?)\s+"
    r"(?P<country>[A-Z]{3})\s+"
    r"(?P<age>\d{1,2})\s+"
    r"(?P<tournaments>\d{1,2})\s+"
    r"(?P<points>\d{1,3}(?:,\d{3})*)"
)
WTA_XML_EVENT_BLOCK_RE = re.compile(
    r"<(?:[A-Za-z0-9_]+:)?Event\b[^>]*>.*?</(?:[A-Za-z0-9_]+:)?Event>",
    flags=re.I | re.S,
)
WTA_XML_EVENT_TYPE_RE = re.compile(
    r"<(?:[A-Za-z0-9_]+:)?EventTypeCode>\s*([^<]+)\s*</(?:[A-Za-z0-9_]+:)?EventTypeCode>",
    flags=re.I,
)
WTA_XML_DRAW_LINE_RE = re.compile(
    r"<(?:[A-Za-z0-9_]+:)?DrawLine\b[^>]*>(.*?)</(?:[A-Za-z0-9_]+:)?DrawLine>",
    flags=re.I | re.S,
)
WTA_XML_PLAYER_ID_RE = re.compile(
    r"<(?:[A-Za-z0-9_]+:)?PlayerId>\s*([^<]+)\s*</(?:[A-Za-z0-9_]+:)?PlayerId>",
    flags=re.I,
)
WTA_PROFILE_SINGLES_JSON_RANK_RE = re.compile(
    r'(?i)(?:"(?:singlesRanking|currentSinglesRanking|singles_rank(?:ing)?)"\s*:\s*"?(\d{1,4})"?)|(?:["&]quot;singles["&]quot;\s*:\s*\{[^{}]{0,300}?["&]quot;rank["&]quot;\s*:\s*["&]quot;(\d{1,4})["&]quot;)'
)
WTA_PROFILE_DOUBLES_JSON_RANK_RE = re.compile(
    r'(?i)(?:"(?:doublesRanking|currentDoublesRanking|doubles_rank(?:ing)?)"\s*:\s*"?(\d{1,4})"?)|(?:["&]quot;doubles["&]quot;\s*:\s*\{[^{}]{0,300}?["&]quot;rank["&]quot;\s*:\s*["&]quot;(\d{1,4})["&]quot;)'
)
WTA_PROFILE_SINGLES_TEXT_RANK_RE = re.compile(
    r"(?i)(?:current\s+)?singles\s+rank(?:ing)?[^0-9#]{0,80}#?\s*(\d{1,3}(?:,\d{3})+|\d{1,4})"
)
WTA_PROFILE_DOUBLES_TEXT_RANK_RE = re.compile(
    r"(?i)(?:current\s+)?doubles\s+rank(?:ing)?[^0-9#]{0,80}#?\s*(\d{1,3}(?:,\d{3})+|\d{1,4})"
)
WTA_PROFILE_LINK_RE = re.compile(
    r'href="(?:https?://www\.wtatennis\.com)?/players/(?P<id>\d+)/(?:[^"]+)"[^>]*>(?P<name>.*?)</a>',
    flags=re.I | re.S,
)
WTA_PLAYER_ROW_RE = re.compile(
    r'<tr[^>]*data-player-id="(?P<id>\d+)"[^>]*data-player-name="(?P<name>[^"]+)"',
    flags=re.I | re.S,
)
WTA_PLAYER_FULL_ROW_RE = re.compile(
    r'<tr(?P<attrs>[^>]*\bdata-player-id="(?P<id>\d+)"[^>]*\bdata-player-name="(?P<name>[^"]+)"[^>]*)>(?P<body>.*?)</tr>',
    flags=re.I | re.S,
)
WTA_PLAYER_ROW_RANK_RE = re.compile(
    r'class="[^"]*\bplayer-row__rank\b[^"]*"[^>]*>\s*(?P<rank>\d{1,4})\s*<',
    flags=re.I | re.S,
)
WTA_PLAYER_ROW_COUNTRY_RE = re.compile(
    r'player-cell__country--(?P<country>[A-Z]{3})|flag--(?P<flag>[A-Z]{3})',
    flags=re.I,
)
MATCH_STATUS_PRIORITY = {
    "F": 60,
    "O": 50,
    "L": 50,
    "P": 50,
    "S": 30,
    "U": 20,
    "C": 10,
}


def fetch_text(url: str, extra_headers: Optional[Dict[str, str]] = None) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (MadridOpenPlayerHub/1.0)",
        "Accept": "application/json,text/html,*/*",
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(
        url,
        headers=headers,
    )
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 * (attempt + 1))

    raise RuntimeError(f"Failed to fetch URL after retries: {url}") from last_error


def fetch_bytes(url: str, extra_headers: Optional[Dict[str, str]] = None) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (MadridOpenPlayerHub/1.0)",
        "Accept": "application/pdf,application/octet-stream,*/*",
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, headers=headers)
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 * (attempt + 1))

    raise RuntimeError(f"Failed to fetch URL after retries: {url}") from last_error


def fetch_json(url: str, extra_headers: Optional[Dict[str, str]] = None) -> dict:
    return json.loads(fetch_text(url, extra_headers=extra_headers))


def clean_text(raw: str) -> str:
    text = html.unescape(TAG_RE.sub(" ", raw))
    return SPACE_RE.sub(" ", text).strip()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "unknown"


def split_name(first: str, last: str) -> str:
    name = f"{first or ''} {last or ''}".strip()
    return SPACE_RE.sub(" ", name)


def name_token_key(value: str) -> Tuple[str, ...]:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_text = re.sub(r"[^a-z0-9-]+", " ", ascii_text)
    tokens = [token for token in ascii_text.split() if token and token not in ROLE_LABELS]
    return tuple(sorted(tokens))


def token_edit_distance_leq_one(left: str, right: str) -> bool:
    if left == right:
        return True

    if abs(len(left) - len(right)) > 1:
        return False

    i = 0
    j = 0
    edits = 0

    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
            continue

        edits += 1
        if edits > 1:
            return False

        if len(left) == len(right):
            i += 1
            j += 1
        elif len(left) > len(right):
            i += 1
        else:
            j += 1

    if i < len(left) or j < len(right):
        edits += 1

    return edits <= 1


def token_sets_approx_equal(left: Tuple[str, ...], right: Tuple[str, ...]) -> bool:
    if len(left) != len(right):
        return False

    used = [False] * len(right)
    for token in left:
        matched = False
        for idx, candidate in enumerate(right):
            if used[idx]:
                continue
            if token_edit_distance_leq_one(token, candidate):
                used[idx] = True
                matched = True
                break
        if not matched:
            return False

    return True


def find_existing_player(registry: Dict[str, dict], name: str, country: str) -> Optional[dict]:
    token_key = name_token_key(name)
    if not token_key:
        return None

    matches = [player for player in registry.values() if name_token_key(player.get("name", "")) == token_key]
    if not matches:
        return None

    if country:
        country_matches = [player for player in matches if (player.get("country") or "").upper() == country.upper()]
        if len(country_matches) == 1:
            return country_matches[0]

    if len(matches) == 1:
        return matches[0]

    return None


def find_existing_player_approx(registry: Dict[str, dict], name: str, country: str) -> Optional[dict]:
    target_tokens = name_token_key(name)
    if not target_tokens:
        return None

    candidates = list(registry.values())
    if country:
        candidates = [player for player in candidates if (player.get("country") or "").upper() == country.upper()]

    matched: List[dict] = []
    for player in candidates:
        candidate_tokens = name_token_key(player.get("name", ""))
        if token_sets_approx_equal(target_tokens, candidate_tokens):
            matched.append(player)

    if len(matched) == 1:
        return matched[0]

    return None


def player_metadata_score(player: dict) -> Tuple[int, int, int, int, int]:
    token_count = len(normalize_name_ascii_tokens(player.get("name", "")))
    return (
        1
        if (
            player.get("ranking") not in (None, "")
            or player.get("singlesRanking") not in (None, "")
            or player.get("doublesRanking") not in (None, "")
        )
        else 0,
        1
        if (
            str(player.get("rankingTag") or "").strip()
            or str(player.get("singlesRankingTag") or "").strip()
            or str(player.get("doublesRankingTag") or "").strip()
        )
        else 0,
        1 if str(player.get("tour") or "").strip() else 0,
        1 if normalize_atp_player_id(player.get("atpPlayerId")) or normalize_wta_player_id(player.get("wtaPlayerId")) else 0,
        token_count,
    )


def should_merge_name_variants(left: dict, right: dict) -> bool:
    left_country = str(left.get("country") or "").strip().upper()
    right_country = str(right.get("country") or "").strip().upper()
    if not left_country or left_country != right_country:
        return False

    left_tokens = normalize_name_ascii_tokens(left.get("name", ""))
    right_tokens = normalize_name_ascii_tokens(right.get("name", ""))
    if len(left_tokens) < 2 or len(right_tokens) < 2:
        return False

    left_set = set(left_tokens)
    right_set = set(right_tokens)
    common = left_set & right_set
    if len(common) < 2:
        return False

    if not (left_set <= right_set or right_set <= left_set):
        return False

    shorter_tokens = left_tokens if len(left_set) <= len(right_set) else right_tokens
    longer_set = right_set if len(left_set) <= len(right_set) else left_set
    if shorter_tokens[0] not in longer_set or shorter_tokens[-1] not in longer_set:
        return False

    return True


def merge_player_records(target: dict, source: dict) -> None:
    if not target.get("country") and source.get("country"):
        target["country"] = source["country"]
    if target.get("ranking") in (None, "") and source.get("ranking") not in (None, ""):
        target["ranking"] = source["ranking"]
    if not str(target.get("rankingTag") or "").strip() and str(source.get("rankingTag") or "").strip():
        target["rankingTag"] = source["rankingTag"]
    for field in ("singlesRanking", "singlesRankingTag", "doublesRanking", "doublesRankingTag"):
        if target.get(field) in (None, "") and source.get(field) not in (None, ""):
            target[field] = source[field]
    if not str(target.get("tour") or "").strip() and str(source.get("tour") or "").strip():
        target["tour"] = source["tour"]
    attach_player_ids(
        target,
        atp_player_id=source.get("atpPlayerId", ""),
        wta_player_id=source.get("wtaPlayerId", ""),
    )


def merge_duplicate_player_variants(registry: Dict[str, dict]) -> Dict[str, str]:
    alias_map: Dict[str, str] = {}

    while True:
        player_ids = list(registry.keys())
        merged = False

        for index, left_id in enumerate(player_ids):
            left = registry.get(left_id)
            if not left:
                continue

            for right_id in player_ids[index + 1 :]:
                right = registry.get(right_id)
                if not right or not should_merge_name_variants(left, right):
                    continue

                left_score = player_metadata_score(left)
                right_score = player_metadata_score(right)
                if right_score > left_score:
                    canonical, duplicate = right, left
                elif left_score > right_score:
                    canonical, duplicate = left, right
                elif len(str(left.get("name") or "")) <= len(str(right.get("name") or "")):
                    canonical, duplicate = left, right
                else:
                    canonical, duplicate = right, left

                merge_player_records(canonical, duplicate)
                alias_map[duplicate["id"]] = canonical["id"]
                registry.pop(duplicate["id"], None)
                merged = True
                break

            if merged:
                break

        if not merged:
            break

    return alias_map


def resolve_alias(alias_map: Dict[str, str], player_id: str) -> str:
    current = str(player_id or "").strip()
    while current in alias_map:
        current = alias_map[current]
    return current


def remap_player_snapshots(items: List[dict], alias_map: Dict[str, str], registry: Dict[str, dict]) -> None:
    if not alias_map:
        return

    for item in items:
        for player in item.get("players", []):
            player_id = resolve_alias(alias_map, player.get("id", ""))
            if not player_id:
                continue

            canonical = registry.get(player_id)
            if not canonical:
                continue

            player["id"] = player_id
            player["name"] = canonical.get("name", player.get("name", ""))
            player["country"] = canonical.get("country", player.get("country", ""))
            if canonical.get("ranking") is not None:
                player["ranking"] = canonical["ranking"]
            else:
                player.pop("ranking", None)
            if canonical.get("rankingTag"):
                player["rankingTag"] = canonical["rankingTag"]
            else:
                player.pop("rankingTag", None)
            for field in ("singlesRanking", "singlesRankingTag", "doublesRanking", "doublesRankingTag"):
                if canonical.get(field) not in (None, ""):
                    player[field] = canonical[field]
                else:
                    player.pop(field, None)
            if canonical.get("tour"):
                player["tour"] = canonical["tour"]
            else:
                player.pop("tour", None)
            if canonical.get("atpPlayerId"):
                player["atpPlayerId"] = canonical["atpPlayerId"]
            else:
                player.pop("atpPlayerId", None)
            if canonical.get("wtaPlayerId"):
                player["wtaPlayerId"] = canonical["wtaPlayerId"]
            else:
                player.pop("wtaPlayerId", None)


def infer_training_session_tour(session: dict) -> str:
    session_tour = str(session.get("tour") or "").strip().upper()
    if session_tour in {"ATP", "WTA"}:
        return session_tour

    tours = {
        str(player.get("tour") or "").strip().upper()
        for player in session.get("players", [])
        if str(player.get("tour") or "").strip()
    }
    tours.discard("")

    if len(tours) == 1:
        return next(iter(tours))
    return ""


def enrich_players_from_training_sessions(registry: Dict[str, dict], training_sessions: List[dict]) -> int:
    applied = 0

    while True:
        changed = False

        for session in training_sessions:
            inferred_tour = infer_training_session_tour(session)
            if not inferred_tour:
                continue

            for snapshot in session.get("players", []):
                player_id = str(snapshot.get("id") or "").strip()
                if not player_id:
                    continue

                player = registry.get(player_id)
                if not player or str(player.get("tour") or "").strip():
                    continue

                player["tour"] = inferred_tour
                applied += 1
                changed = True

        if not changed:
            break

    return applied


def infer_tour_from_label(value: object) -> str:
    text = str(value or "").strip().upper()
    if re.search(r"\bATP\b", text):
        return "ATP"
    if re.search(r"\bWTA\b", text):
        return "WTA"
    return ""


def upsert_player(registry: Dict[str, dict], name: str, country: str) -> Optional[dict]:
    name = SPACE_RE.sub(" ", (name or "").strip())
    country = (country or "").strip().upper()

    if not name:
        return None

    player_id = slugify(name)
    current = registry.get(player_id)

    if current is None:
        current = {"id": player_id, "name": name, "country": country}
        registry[player_id] = current
    else:
        if not current.get("country") and country:
            current["country"] = country

    return {"id": current["id"], "name": current["name"], "country": current.get("country", "")}


def normalize_country(raw: str) -> str:
    cleaned = clean_text(raw).strip().strip("()").upper()
    match = re.search(r"[A-Z]{3}", cleaned)
    return match.group(0) if match else cleaned


def normalize_directory_name(raw: str) -> str:
    name = clean_text(raw)
    name = PLAYER_NAME_PREFIX_RE.sub("", name)
    return SPACE_RE.sub(" ", name).strip()


def parse_directory_name_and_ranking_tag(raw: str) -> Tuple[str, str]:
    name = clean_text(raw)
    tags: List[str] = []

    while True:
        match = PLAYER_NAME_PREFIX_TOKEN_RE.match(name)
        if not match:
            break
        tag = SPACE_RE.sub(" ", match.group(1) or "").strip().upper()
        if tag:
            tags.append(tag)
        name = name[match.end() :].strip()

    normalized_name = SPACE_RE.sub(" ", name).strip()

    ranking_tag = ""
    if any(tag == "PR" for tag in tags):
        ranking_tag = "PR"

    return normalized_name, ranking_tag


def infer_discipline(draw_code: str) -> str:
    code = (draw_code or "").upper()
    if code.endswith("S"):
        return "singles"
    if code.endswith("D"):
        return "doubles"
    return "unknown"


def format_round_label(draw_code: str, round_code: str) -> str:
    draw = (draw_code or "").strip().upper()
    code = (round_code or "").strip().upper()

    if draw in {"QS", "QD"}:
        if code in {"Q1", "R1"}:
            return "资格赛第一轮"
        if code in {"Q2", "R2"}:
            return "资格赛第二轮"
        if code in {"Q3", "R3"}:
            return "资格赛第三轮"
        return code or "-"

    if draw in {"MS", "MD"}:
        if code in {"R128", "R1"}:
            return "第一轮"
        if code in {"R64", "R2", "R6"}:
            return "第二轮"
        if code in {"R32"} and draw == "MD":
            return "第一轮"
        if code in {"R32", "R3"}:
            return "第三轮"
        if code in {"R16", "R4"}:
            return "16强"
        if code in {"QF", "R5"}:
            return "8强"
        if code == "SF":
            return "半决赛"
        if code == "F":
            return "决赛"
        return code or "-"

    return code or "-"


def parse_int(value: object) -> Optional[int]:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed


def parse_rank_number(value: object) -> Optional[int]:
    text = str(value or "").strip()
    if not text:
        return None
    return parse_int(text.replace(",", ""))


def normalize_atp_player_id(value: object) -> str:
    text = str(value or "").strip().upper()
    if re.fullmatch(r"[A-Z0-9]{4}", text):
        return text
    return ""


def normalize_wta_player_id(value: object) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"\d{3,10}", text):
        return text
    return ""


def attach_player_ids(player: dict, atp_player_id: object = "", wta_player_id: object = "") -> bool:
    changed = False

    normalized_atp_id = normalize_atp_player_id(atp_player_id)
    if normalized_atp_id and not str(player.get("atpPlayerId") or "").strip():
        player["atpPlayerId"] = normalized_atp_id
        if not str(player.get("tour") or "").strip():
            player["tour"] = "ATP"
        changed = True

    normalized_wta_id = normalize_wta_player_id(wta_player_id)
    if normalized_wta_id and not str(player.get("wtaPlayerId") or "").strip():
        player["wtaPlayerId"] = normalized_wta_id
        if not str(player.get("tour") or "").strip():
            player["tour"] = "WTA"
        changed = True

    return changed


def slugify_path_segment(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def parse_wta_profile_ranking(html_text: str, discipline: str = "singles") -> Optional[int]:
    json_re = WTA_PROFILE_DOUBLES_JSON_RANK_RE if normalize_ranking_discipline(discipline) == "doubles" else WTA_PROFILE_SINGLES_JSON_RANK_RE
    text_re = WTA_PROFILE_DOUBLES_TEXT_RANK_RE if normalize_ranking_discipline(discipline) == "doubles" else WTA_PROFILE_SINGLES_TEXT_RANK_RE

    for match in json_re.finditer(html_text):
        rank = parse_rank_number(next((group for group in match.groups() if group), None))
        if rank is not None and 0 < rank < 5000:
            return rank

    cleaned_text = clean_text(html_text)
    for match in text_re.finditer(cleaned_text):
        rank = parse_rank_number(match.group(1))
        if rank is not None and 0 < rank < 5000:
            return rank

    return None


def parse_wta_profile_singles_ranking(html_text: str) -> Optional[int]:
    return parse_wta_profile_ranking(html_text, "singles")


def parse_wta_profile_doubles_ranking(html_text: str) -> Optional[int]:
    return parse_wta_profile_ranking(html_text, "doubles")


def fetch_wta_profile_singles_ranking(wta_player_id: str, player_name: str) -> Optional[int]:
    rankings = fetch_wta_profile_rankings(wta_player_id, player_name)
    return rankings.get("singles")


def fetch_wta_profile_rankings(wta_player_id: str, player_name: str) -> Dict[str, Optional[int]]:
    normalized_id = normalize_wta_player_id(wta_player_id)
    if not normalized_id:
        return {"singles": None, "doubles": None}

    slug = slugify_path_segment(player_name)
    urls = []
    if slug:
        urls.append(f"https://www.wtatennis.com/players/{normalized_id}/{slug}")
    urls.append(f"https://www.wtatennis.com/players/{normalized_id}")

    for url in urls:
        try:
            html_text = fetch_text(url)
        except Exception:
            continue

        rankings = {
            "singles": parse_wta_profile_singles_ranking(html_text),
            "doubles": parse_wta_profile_doubles_ranking(html_text),
        }
        if rankings["singles"] is not None or rankings["doubles"] is not None:
            return rankings

    return {"singles": None, "doubles": None}


def apply_player_id_overrides(registry: Dict[str, dict]) -> int:
    applied = 0

    for player in registry.values():
        normalized_name = slugify_path_segment(str(player.get("name") or ""))
        override_atp_id = ATP_PLAYER_ID_OVERRIDES.get(normalized_name)
        override_wta_id = WTA_PLAYER_ID_OVERRIDES.get(normalized_name)
        if not override_atp_id and not override_wta_id:
            continue

        if attach_player_ids(player, atp_player_id=override_atp_id, wta_player_id=override_wta_id):
            applied += 1

    return applied


def apply_atp_ranking_overrides(registry: Dict[str, dict]) -> int:
    applied = 0

    for player in registry.values():
        atp_player_id = normalize_atp_player_id(player.get("atpPlayerId"))
        if not atp_player_id:
            continue

        rank = ATP_RANKING_OVERRIDES_BY_ID.get(atp_player_id)
        if rank is None or player.get("ranking") not in (None, ""):
            continue

        set_player_ranking(player, rank, "", "singles")
        player["tour"] = player.get("tour") or "ATP"
        applied += 1

    return applied


def normalize_person_name(raw: str) -> str:
    cleaned = SPACE_RE.sub(" ", str(raw or "").strip())
    return cleaned


def normalize_name_ascii_tokens(raw: str) -> List[str]:
    normalized = unicodedata.normalize("NFKD", str(raw or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_text = re.sub(r"[^a-z0-9]+", " ", ascii_text)
    return [token for token in ascii_text.split() if token]


def parse_ranking_hint(raw_rank: object, raw_tag: object = "") -> Tuple[Optional[int], str]:
    rank: Optional[int] = None
    tag = ""

    raw_tag_text = str(raw_tag or "").strip().upper()
    if raw_tag_text == "PR":
        tag = "PR"

    if isinstance(raw_rank, (int, float)):
        candidate = int(raw_rank)
        if candidate > 0:
            rank = candidate
        return rank, tag

    text = str(raw_rank or "").strip()
    if not text:
        return rank, tag

    upper_text = text.upper()
    if "PR" in upper_text:
        tag = "PR"

    match = RANK_NUMBER_RE.search(upper_text)
    if match:
        candidate = int(match.group(1))
        if candidate > 0:
            rank = candidate

    return rank, tag


def normalize_ranking_discipline(value: object) -> str:
    text = str(value or "").strip().lower()
    return "doubles" if text == "doubles" else "singles"


def set_player_ranking(
    player: dict,
    rank: Optional[int],
    tag: str = "",
    discipline: str = "singles",
    replace: bool = False,
) -> bool:
    if rank is None or rank <= 0:
        return False

    normalized_discipline = normalize_ranking_discipline(discipline)
    normalized_tag = str(tag or "").strip().upper()
    rank_field = f"{normalized_discipline}Ranking"
    tag_field = f"{normalized_discipline}RankingTag"
    changed = False

    current = parse_int(player.get(rank_field))
    if replace:
        should_update_rank = current != rank
    else:
        should_update_rank = current is None or rank < current
    if should_update_rank:
        player[rank_field] = rank
        changed = True

    if replace:
        if normalized_tag:
            if player.get(tag_field) != normalized_tag:
                player[tag_field] = normalized_tag
                changed = True
        elif tag_field in player:
            player.pop(tag_field, None)
            changed = True
    elif normalized_tag and not str(player.get(tag_field) or "").strip():
        player[tag_field] = normalized_tag
        changed = True

    primary_tag = normalized_tag
    if normalized_discipline == "doubles" and not primary_tag:
        primary_tag = "D"

    current_primary = parse_int(player.get("ranking"))
    current_primary_tag = str(player.get("rankingTag") or "").strip().upper()
    should_update_primary = current_primary is None
    if normalized_discipline == "singles":
        if replace:
            should_update_primary = (
                current_primary != rank
                or current_primary_tag == "D"
                or current_primary_tag != primary_tag
            )
        elif current_primary_tag == "D":
            should_update_primary = True

    if should_update_primary:
        player["ranking"] = rank
        if primary_tag:
            player["rankingTag"] = primary_tag
        else:
            player.pop("rankingTag", None)
        changed = True

    return changed


def apply_ranking_hint(player: dict, raw_rank: object, raw_tag: object = "", discipline: str = "singles") -> bool:
    rank, tag = parse_ranking_hint(raw_rank, raw_tag)
    changed = False

    if rank is not None:
        changed = set_player_ranking(player, rank, tag, discipline) or changed

    return changed


def parse_atp_official_ranking_rows(html_text: str) -> List[dict]:
    rows: List[dict] = []
    seen = set()

    for row_html in TABLE_ROW_RE.findall(html_text):
        cells = TABLE_CELL_RE.findall(row_html)
        if len(cells) < 2:
            continue

        rank = parse_rank_number(clean_text(cells[0]))
        if rank is None or rank <= 0:
            continue

        player_name = ""
        atp_player_id = ""
        for link_match in ATP_PLAYER_LINK_RE.finditer(row_html):
            candidate = normalize_person_name(clean_text(link_match.group("name")))
            if not candidate or candidate.lower().startswith("image"):
                continue
            player_name = candidate
            atp_player_id = normalize_atp_player_id(link_match.group("id"))
            break

        if not player_name:
            player_name = normalize_person_name(clean_text(cells[1]))
        if not player_name:
            continue

        key = (rank, player_name, atp_player_id)
        if key in seen:
            continue

        seen.add(key)
        rows.append(
            {
                "ranking": rank,
                "name": player_name,
                "abbr": player_name,
                "atpPlayerId": atp_player_id,
            }
        )

    return rows


def parse_atp_ranking_report_rows(report_text: str) -> List[dict]:
    rows: List[dict] = []
    seen = set()

    for match in ATP_RANKING_REPORT_ROW_RE.finditer(report_text):
        rank = parse_int(match.group("rank"))
        if rank is None or rank <= 0:
            continue

        first_name = normalize_person_name(match.group("first"))
        last_name = normalize_person_name(match.group("last"))
        name = normalize_person_name(f"{first_name} {last_name}")
        if not name:
            continue

        country = normalize_country(match.group("country") or "")
        key = (rank, name, country)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "ranking": rank,
                "name": name,
                "country": country,
            }
        )

    return rows


def parse_atp_profile_rankings(html_text: str) -> Dict[str, Optional[int]]:
    rankings: Dict[str, Optional[int]] = {"singles": None, "doubles": None}

    singles_match = ATP_PROFILE_SINGLES_JSON_RANK_RE.search(html_text)
    if singles_match:
        rankings["singles"] = parse_rank_number(singles_match.group(1))

    doubles_match = ATP_PROFILE_DOUBLES_JSON_RANK_RE.search(html_text)
    if doubles_match:
        rankings["doubles"] = parse_rank_number(doubles_match.group(1))

    dom_ranks = [
        rank
        for rank in (parse_rank_number(match.group("rank")) for match in ATP_PROFILE_RANK_STAT_RE.finditer(html_text))
        if rank is not None and 0 < rank < 5000
    ]
    if rankings["singles"] is None and dom_ranks:
        rankings["singles"] = dom_ranks[0]
    if rankings["doubles"] is None and len(dom_ranks) > 1:
        rankings["doubles"] = dom_ranks[1]

    return rankings


def is_cloudflare_challenge_page(html_text: str) -> bool:
    lowered = html_text.lower()
    return "challenges.cloudflare.com" in lowered or "just a moment..." in lowered


def fetch_atp_profile_rankings(atp_player_id: str) -> Dict[str, Optional[int]]:
    normalized_id = normalize_atp_player_id(atp_player_id)
    if not normalized_id:
        return {"singles": None, "doubles": None}

    url = ATP_PLAYER_PROFILE_URL_TEMPLATE.format(atp_player_id=normalized_id.lower())
    html_text = fetch_text(url)
    if is_cloudflare_challenge_page(html_text):
        raise RuntimeError("ATP profile page returned a Cloudflare challenge")
    return parse_atp_profile_rankings(html_text)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("pypdf is required to parse ATP ranking report PDFs") from error

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def find_player_by_atp_id(registry: Dict[str, dict], atp_player_id: object) -> Optional[dict]:
    normalized_id = normalize_atp_player_id(atp_player_id)
    if not normalized_id:
        return None

    for player in registry.values():
        if normalize_atp_player_id(player.get("atpPlayerId")) == normalized_id:
            return player
    return None


def resolve_atp_ranking_row_to_player(registry: Dict[str, dict], row: dict) -> Optional[dict]:
    player = find_player_by_atp_id(registry, row.get("atpPlayerId"))
    if player:
        return player

    name = str(row.get("name") or row.get("abbr") or "").strip()
    country = str(row.get("country") or "").strip()
    if not name:
        return None

    if re.match(r"^[A-Z]\.\s+", normalize_person_name(name)):
        return resolve_atp_abbr_to_player(registry, name)

    player = find_existing_player(registry, name, country)
    if player:
        return player
    return find_existing_player_approx(registry, name, country)


def resolve_atp_abbr_to_player(registry: Dict[str, dict], abbr_name: str) -> Optional[dict]:
    abbr_text = normalize_person_name(abbr_name)
    match = re.match(r"^([A-Z])\.\s+(.+)$", abbr_text)
    if not match:
        return None

    initial = match.group(1).lower()
    last_name_part = match.group(2)
    last_tokens = normalize_name_ascii_tokens(last_name_part)
    if not last_tokens:
        return None

    candidates: List[Tuple[int, dict]] = []
    for player in registry.values():
        tour = str(player.get("tour") or "").upper()
        if tour and tour != "ATP":
            continue

        tokens = normalize_name_ascii_tokens(player.get("name", ""))
        if not tokens:
            continue
        if not tokens[0].startswith(initial):
            continue

        score = -1
        if tokens[-len(last_tokens) :] == last_tokens:
            score = 3
        else:
            for idx in range(0, len(tokens) - len(last_tokens) + 1):
                if tokens[idx : idx + len(last_tokens)] == last_tokens:
                    score = 2
                    break
            if score < 0 and last_tokens[-1] == tokens[-1]:
                score = 1

        if score > 0:
            candidates.append((score, player))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    top_score = candidates[0][0]
    top = [player for score, player in candidates if score == top_score]
    if len(top) != 1:
        return None
    return top[0]


def parse_wta_official_rankings(html_text: str) -> List[dict]:
    profile_id_by_name_token: Dict[Tuple[str, ...], str] = {}
    for match in WTA_PROFILE_LINK_RE.finditer(html_text):
        name = normalize_person_name(clean_text(match.group("name") or ""))
        player_id = normalize_wta_player_id(match.group("id"))
        token_key = name_token_key(name)
        if not token_key or not player_id:
            continue
        if token_key not in profile_id_by_name_token:
            profile_id_by_name_token[token_key] = player_id

    text = clean_text(html_text)
    entries: List[dict] = []
    seen = set()

    for match in WTA_RANKING_ROW_RE.finditer(text):
        rank = parse_int(match.group("rank"))
        name = normalize_person_name(match.group("name"))
        country = str(match.group("country") or "").strip().upper()
        if rank is None or rank <= 0 or not name:
            continue
        if "Ranking" in name or "Form" in name:
            continue

        key = (name_token_key(name), country)
        if not key[0] or key in seen:
            continue

        seen.add(key)
        entries.append(
            {
                "name": name,
                "country": country,
                "ranking": rank,
                "tour": "WTA",
                "rankingTag": "",
                "wtaPlayerId": profile_id_by_name_token.get(name_token_key(name), ""),
            }
        )

    for match in WTA_PLAYER_FULL_ROW_RE.finditer(html_text):
        player_id = normalize_wta_player_id(match.group("id"))
        name = normalize_person_name(html.unescape(match.group("name") or ""))
        body = match.group("body") or ""
        rank_match = WTA_PLAYER_ROW_RANK_RE.search(body)
        rank = parse_int(rank_match.group("rank") if rank_match else None)
        if rank is None or rank <= 0 or not name:
            continue

        country = ""
        country_match = WTA_PLAYER_ROW_COUNTRY_RE.search(body)
        if country_match:
            country = str(country_match.group("country") or country_match.group("flag") or "").upper()

        key = (name_token_key(name), country)
        if not key[0] or key in seen:
            continue

        seen.add(key)
        entries.append(
            {
                "name": name,
                "country": country,
                "ranking": rank,
                "tour": "WTA",
                "rankingTag": "",
                "wtaPlayerId": player_id,
            }
        )

    return entries


def parse_wta_official_profile_entries(html_text: str) -> List[dict]:
    entries: List[dict] = []
    seen = set()

    for match in WTA_PLAYER_ROW_RE.finditer(html_text):
        name = normalize_person_name(match.group("name"))
        player_id = normalize_wta_player_id(match.group("id"))
        token_key = name_token_key(name)
        if not token_key or not player_id or token_key in seen:
            continue

        seen.add(token_key)
        entries.append(
            {
                "name": name,
                "country": "",
                "tour": "WTA",
                "rankingTag": "",
                "wtaPlayerId": player_id,
            }
        )

    for match in WTA_PROFILE_LINK_RE.finditer(html_text):
        name = normalize_person_name(clean_text(match.group("name") or ""))
        player_id = normalize_wta_player_id(match.group("id"))
        token_key = name_token_key(name)
        if not token_key or not player_id or token_key in seen:
            continue

        seen.add(token_key)
        entries.append(
            {
                "name": name,
                "country": "",
                "tour": "WTA",
                "rankingTag": "",
                "wtaPlayerId": player_id,
            }
        )

    return entries


def extract_wta_ranking_value(row: dict, side: str) -> object:
    side_upper = (side or "").upper()
    preferred = (
        f"PlayerRank{side_upper}",
        f"PlayerRanking{side_upper}",
        f"Rank{side_upper}",
        f"Ranking{side_upper}",
        f"PlayerWtaRank{side_upper}",
        f"PlayerWtaRanking{side_upper}",
        f"WtaRank{side_upper}",
        f"WtaRanking{side_upper}",
        f"PlayerSinglesRank{side_upper}",
        f"PlayerSinglesRanking{side_upper}",
        f"SinglesRank{side_upper}",
        f"SinglesRanking{side_upper}",
    )
    for key in preferred:
        if key in row:
            return row.get(key)

    side_lower = side_upper.lower()
    for key, value in row.items():
        key_lower = key.lower()
        if "rank" not in key_lower or "seed" in key_lower:
            continue
        if side_lower not in key_lower:
            continue
        return value

    return None


def extract_wta_ranking_tag(row: dict, side: str) -> object:
    side_upper = (side or "").upper()
    candidates = (
        f"PlayerRankTag{side_upper}",
        f"PlayerRankingTag{side_upper}",
        f"RankTag{side_upper}",
        f"RankingTag{side_upper}",
    )
    for key in candidates:
        if key in row:
            return row.get(key)
    return ""


def is_wta_singles_row(row: dict) -> bool:
    draw_level = str(row.get("DrawLevelType") or row.get("DrawLevel") or "").strip().upper()
    draw_match_type = str(row.get("DrawMatchType") or row.get("MatchType") or "").strip().upper()
    draw_code = f"{draw_level}{draw_match_type}"

    if draw_match_type in {"S", "LS", "RS"}:
        return True
    return infer_discipline(draw_code) == "singles"


def extract_atp_team_ranking_value(team: dict, role: str) -> object:
    role_key = "partner" if role == "partner" else "player"
    preferred: List[str] = []

    if role_key == "player":
        preferred = [
            "PlayerRank",
            "PlayerRanking",
            "PlayerSinglesRank",
            "PlayerSinglesRanking",
            "CurrentRank",
            "CurrentRanking",
            "WorldRank",
            "WorldRanking",
        ]
    else:
        preferred = [
            "PartnerRank",
            "PartnerRanking",
            "PartnerSinglesRank",
            "PartnerSinglesRanking",
        ]

    for key in preferred:
        if key in team:
            return team.get(key)

    for key, value in team.items():
        key_lower = key.lower()
        if "rank" not in key_lower or "seed" in key_lower:
            continue
        if role_key == "player" and "partner" in key_lower:
            continue
        if role_key == "partner" and "partner" not in key_lower:
            continue
        return value

    return None


def extract_atp_draw_player_name(draw_player: dict) -> str:
    first_name = (
        draw_player.get("FirstNameFull")
        or draw_player.get("FirstName")
        or draw_player.get("PlayerFirstNameFull")
        or draw_player.get("PlayerFirstName")
        or ""
    )
    last_name = draw_player.get("LastName") or draw_player.get("PlayerLastName") or ""
    full_name = split_name(first_name, last_name)
    if full_name:
        return full_name

    for key in ("DisplayName", "PlayerName", "Name"):
        value = normalize_person_name(draw_player.get(key))
        if value:
            return value

    return ""


def extract_atp_draw_player_country(draw_player: dict) -> str:
    for key in ("Nationality", "CountryCode", "PlayerCountryCode", "Country"):
        value = normalize_country(str(draw_player.get(key) or ""))
        if value:
            return value
    return ""


def normalize_schedule_type(raw: str) -> str:
    label = (raw or "").strip().lower()
    if label in {"starts at", "starts at."}:
        return "starts_at"
    if label == "not before":
        return "not_before"
    if label == "followed by":
        return "followed_by"
    if label == "after suitable rest":
        return "after_rest"
    return "unknown"


def build_start_time_from_schedule(day_raw: str, clock_raw: str) -> str:
    day = (day_raw or "").split("T")[0].strip()
    clock = (clock_raw or "").strip()
    if not day or not clock:
        return ""

    clock_match = ISO_CLOCK_RE.match(clock)
    if not clock_match:
        return ""

    hour, minute, second, tz_hour, tz_minute = clock_match.groups()
    second = second or "00"
    return f"{day}T{hour}:{minute}:{second}{tz_hour}:{tz_minute}"


def should_override_start_time(current_start_time: str, status: str) -> bool:
    current = (current_start_time or "").strip()
    if not current:
        return True
    if "T23:59" in current:
        return True

    status_code = (status or "").strip().upper()
    if status_code in {"", "U", "S"} and MIDNIGHT_TIME_RE.search(current):
        return True

    return False


def has_score_payload(value: object) -> bool:
    text = str(value or "").strip()
    if not text or text == "-":
        return False
    return any(char.isdigit() for char in text)


def match_status_priority(status: str) -> int:
    code = (status or "").strip().upper()
    return MATCH_STATUS_PRIORITY.get(code, 0)


def match_richness_score(match: dict) -> int:
    score = 0

    if has_score_payload(match.get("score")):
        score += 8
    if str(match.get("result") or "").strip():
        score += 5
    if str(match.get("court") or "").strip():
        score += 2
    if str(match.get("roundCode") or "").strip() and str(match.get("roundCode") or "").strip() != "-":
        score += 2

    start_time = str(match.get("startTime") or "").strip()
    if start_time and not should_override_start_time(start_time, str(match.get("status") or "")):
        score += 2

    players = match.get("players") or []
    if len(players) >= 2:
        score += 1

    return score


def merge_match_payload(primary: dict, secondary: dict) -> None:
    for field in ("score", "result", "court", "round", "roundCode", "roundLabel", "draw", "discipline"):
        if not str(primary.get(field) or "").strip() and str(secondary.get(field) or "").strip():
            primary[field] = secondary[field]

    if not primary.get("players") and secondary.get("players"):
        primary["players"] = secondary["players"]

    if not str(primary.get("status") or "").strip() and str(secondary.get("status") or "").strip():
        primary["status"] = secondary["status"]

    secondary_start = str(secondary.get("startTime") or "").strip()
    if secondary_start and should_override_start_time(str(primary.get("startTime") or ""), str(primary.get("status") or "")):
        primary["startTime"] = secondary_start


def dedupe_matches_by_id(items: List[dict]) -> List[dict]:
    deduped: Dict[str, dict] = {}
    ordered_ids: List[str] = []
    passthrough: List[dict] = []

    for item in items:
        match_id = str(item.get("id") or "").strip()
        if not match_id:
            passthrough.append(item)
            continue

        current = deduped.get(match_id)
        if current is None:
            deduped[match_id] = item
            ordered_ids.append(match_id)
            continue

        current_rank = match_status_priority(str(current.get("status") or ""))
        incoming_rank = match_status_priority(str(item.get("status") or ""))
        current_score = match_richness_score(current)
        incoming_score = match_richness_score(item)

        keep_current = True
        if incoming_rank > current_rank:
            keep_current = False
        elif incoming_rank == current_rank and incoming_score > current_score:
            keep_current = False

        if keep_current:
            merge_match_payload(current, item)
        else:
            merge_match_payload(item, current)
            deduped[match_id] = item

    return [deduped[match_id] for match_id in ordered_ids] + passthrough


def parse_matches(payload: dict, registry: Dict[str, dict]) -> List[dict]:
    rows = payload.get("matches") or []
    parsed: List[dict] = []

    for row in rows:
        players: List[dict] = []

        for side in ("A", "A2", "B", "B2"):
            name = split_name(row.get(f"PlayerNameFirst{side}", ""), row.get(f"PlayerNameLast{side}", ""))
            country = row.get(f"PlayerCountry{side}", "")
            wta_player_id = row.get(f"PlayerID{side}", "")
            player = upsert_player(registry, name, country)
            if player:
                canonical = registry.get(player["id"])
                if canonical:
                    attach_player_ids(canonical, wta_player_id=wta_player_id)
                    canonical["tour"] = canonical.get("tour") or "WTA"
                    if canonical.get("ranking") is not None:
                        player["ranking"] = canonical["ranking"]
                    if canonical.get("rankingTag"):
                        player["rankingTag"] = canonical["rankingTag"]
                    if canonical.get("tour"):
                        player["tour"] = canonical["tour"]
                    if canonical.get("wtaPlayerId"):
                        player["wtaPlayerId"] = canonical["wtaPlayerId"]
                player["side"] = "A" if side.startswith("A") else "B"
                players.append(player)

        if not players:
            continue

        round_id = str(row.get("RoundID") or "").strip()
        draw_level = (row.get("DrawLevelType") or "").strip()
        draw_match_type = (row.get("DrawMatchType") or "").strip()
        draw_code = f"{draw_level}{draw_match_type}"
        round_code = f"R{round_id}" if round_id else "-"

        parsed.append(
            {
                "id": str(row.get("MatchID") or "").strip(),
                "startTime": row.get("MatchTimeStamp") or "",
                "status": str(row.get("MatchState") or "").strip(),
                "round": round_code,
                "roundCode": round_code,
                "roundLabel": format_round_label(draw_code, round_code),
                "draw": draw_code,
                "discipline": infer_discipline(draw_code),
                "tour": "WTA",
                "court": f"Court {row.get('CourtID')}" if row.get("CourtID") is not None else "",
                "score": str(row.get("ScoreString") or "").strip(),
                "result": str(row.get("ResultString") or "").strip(),
                "players": players,
            }
        )

    return dedupe_matches_by_id(parsed)


def parse_atp_matches(payload: dict, registry: Dict[str, dict]) -> List[dict]:
    rows = payload.get("Matches") or []
    parsed: List[dict] = []

    for row in rows:
        players: List[dict] = []
        match_id = str(row.get("MatchId") or "").strip()
        draw_code = match_id[:2]
        discipline = infer_discipline(draw_code)

        for team_key, side in (("PlayerTeam1", "A"), ("PlayerTeam2", "B")):
            team = row.get(team_key) or {}
            primary_atp_id = team.get("PlayerId")
            partner_atp_id = team.get("PartnerId")

            primary_name = split_name(team.get("PlayerFirstNameFull") or team.get("PlayerFirstName"), team.get("PlayerLastName"))
            primary_country = team.get("PlayerCountryCode") or ""
            primary_player = upsert_player(registry, primary_name, primary_country)
            if primary_player:
                canonical_primary = registry.get(primary_player["id"])
                if canonical_primary:
                    attach_player_ids(canonical_primary, atp_player_id=primary_atp_id)
                    canonical_primary["tour"] = canonical_primary.get("tour") or "ATP"
                    apply_ranking_hint(canonical_primary, extract_atp_team_ranking_value(team, "player"), discipline=discipline)
                    if canonical_primary.get("ranking") is not None:
                        primary_player["ranking"] = canonical_primary["ranking"]
                    if canonical_primary.get("rankingTag"):
                        primary_player["rankingTag"] = canonical_primary["rankingTag"]
                    if canonical_primary.get("tour"):
                        primary_player["tour"] = canonical_primary["tour"]
                    if canonical_primary.get("atpPlayerId"):
                        primary_player["atpPlayerId"] = canonical_primary["atpPlayerId"]
                primary_player["side"] = side
                players.append(primary_player)

            partner_name = split_name(team.get("PartnerFirstNameFull") or team.get("PartnerFirstName"), team.get("PartnerLastName"))
            partner_country = team.get("PartnerCountryCode") or ""
            partner_player = upsert_player(registry, partner_name, partner_country)
            if partner_player:
                canonical_partner = registry.get(partner_player["id"])
                if canonical_partner:
                    attach_player_ids(canonical_partner, atp_player_id=partner_atp_id)
                    canonical_partner["tour"] = canonical_partner.get("tour") or "ATP"
                    apply_ranking_hint(canonical_partner, extract_atp_team_ranking_value(team, "partner"), discipline=discipline)
                    if canonical_partner.get("ranking") is not None:
                        partner_player["ranking"] = canonical_partner["ranking"]
                    if canonical_partner.get("rankingTag"):
                        partner_player["rankingTag"] = canonical_partner["rankingTag"]
                    if canonical_partner.get("tour"):
                        partner_player["tour"] = canonical_partner["tour"]
                    if canonical_partner.get("atpPlayerId"):
                        partner_player["atpPlayerId"] = canonical_partner["atpPlayerId"]
                partner_player["side"] = side
                players.append(partner_player)

        if not players:
            continue

        round_short = ((row.get("Round") or {}).get("ShortName") or "").strip()
        round_code = round_short or "-"

        parsed.append(
            {
                "id": f"ATP-{match_id}" if match_id else "",
                "startTime": row.get("MatchDate") or "",
                "status": str(row.get("Status") or "").strip(),
                "round": round_code,
                "roundCode": round_code,
                "roundLabel": format_round_label(draw_code, round_code),
                "draw": draw_code,
                "discipline": discipline,
                "tour": "ATP",
                "court": str(row.get("CourtName") or "").strip(),
                "score": str(row.get("ResultString") or "").strip(),
                "result": str(row.get("ResultString") or "").strip(),
                "players": players,
            }
        )

    return dedupe_matches_by_id(parsed)


def parse_atp_schedule(payload: dict) -> Dict[str, dict]:
    schedule_map: Dict[str, dict] = {}
    rows = payload.get("DailySchedule") or []

    for day in rows:
        day_value = str(day.get("IsoDate") or "").split("T")[0]

        for court in day.get("Courts") or []:
            court_name = str(court.get("Name") or "").strip()

            for match in court.get("Matches") or []:
                match_id = str(match.get("MatchId") or "").strip()
                if not match_id:
                    continue

                not_before_text = str(match.get("NotBeforeText") or "").strip()
                not_before_time = str(match.get("NotBeforeISOTime") or "").strip()

                schedule_map[f"ATP-{match_id}"] = {
                    "day": day_value,
                    "court": court_name,
                    "order": parse_int(match.get("CourtSeq")),
                    "type": normalize_schedule_type(not_before_text),
                    "text": not_before_text,
                    "time": not_before_time,
                    "display": str(match.get("NotBeforeForDisplay") or "").strip(),
                }

    return schedule_map


def parse_wta_schedule(payload: dict) -> Dict[str, dict]:
    schedule_map: Dict[str, dict] = {}
    data = payload.get("Data") or {}

    for day in data.get("ScheduleDays") or []:
        day_value = str(day.get("MatchDate") or "").split("T")[0]

        for court in day.get("ScheduleCourts") or []:
            court_name = str(court.get("CourtName") or "").strip()

            for match in court.get("ScheduleMatches") or []:
                match_id = str(match.get("MatchId") or "").strip()
                if not match_id:
                    continue

                not_before_text = str(match.get("NotBeforeText") or "").strip()
                display_time = str(match.get("DisplayTime") or "").strip()
                round_info = match.get("Round") or {}
                round_code = str(round_info.get("ShortName") or "").strip()

                schedule_map[match_id] = {
                    "day": day_value,
                    "court": court_name,
                    "order": parse_int(match.get("MatchSequence")),
                    "type": normalize_schedule_type(not_before_text),
                    "text": not_before_text,
                    "time": str(match.get("DisplayIsoTime") or "").strip(),
                    "display": display_time,
                    "roundCode": round_code,
                }

    return schedule_map


def merge_schedule_into_matches(matches: List[dict], schedule_map: Dict[str, dict]) -> None:
    for match in matches:
        match_id = str(match.get("id") or "").strip()
        if not match_id:
            continue

        schedule = schedule_map.get(match_id)
        if not schedule:
            continue

        if not str(match.get("court") or "").strip() and schedule.get("court"):
            match["court"] = schedule["court"]

        if schedule.get("day"):
            match["scheduleDay"] = schedule["day"]
        if schedule.get("order") is not None:
            match["scheduleOrder"] = schedule["order"]
        if schedule.get("type"):
            match["scheduleType"] = schedule["type"]
        if schedule.get("text"):
            match["scheduleText"] = schedule["text"]
        if schedule.get("time"):
            match["scheduleTime"] = schedule["time"]
        if schedule.get("display"):
            match["scheduleDisplay"] = schedule["display"]
        if schedule.get("roundCode") and str(match.get("discipline") or "").lower() == "doubles":
            round_code = str(schedule["roundCode"]).strip()
            match["round"] = round_code
            match["roundCode"] = round_code
            match["roundLabel"] = format_round_label(str(match.get("draw") or ""), round_code)

        replacement_start = build_start_time_from_schedule(schedule.get("day", ""), schedule.get("time", ""))
        if replacement_start and should_override_start_time(str(match.get("startTime") or ""), str(match.get("status") or "")):
            match["startTime"] = replacement_start


def extract_training_fragments(cell_html: str) -> List[str]:
    fragments = TRAINING_BLOCK_RE.findall(cell_html)
    if fragments:
        return fragments
    return [cell_html] if clean_text(cell_html) else []


def parse_training_person(cell_html: str, registry: Dict[str, dict]) -> Optional[dict]:
    country_match = SMALL_RE.search(cell_html)
    country = clean_text(country_match.group(1)) if country_match else ""
    name = clean_text(cell_html)

    if country:
        name = re.sub(rf"\b{re.escape(country)}\b", "", name, flags=re.I).strip()

    if name.lower() in ROLE_LABELS or name in {"", "TBC", "Tbd", "TBA", "Tba"}:
        return None

    existing = find_existing_player(registry, name, country)
    if existing:
        return {"id": existing["id"], "name": existing["name"], "country": existing.get("country", "")}

    return upsert_player(registry, name, country)


def parse_training_day(html_text: str, day_offset: int, registry: Dict[str, dict]) -> Tuple[str, List[dict]]:
    day_label_match = re.search(
        r'<div class="scheduleDay[^>]*>\s*<span>(.*?)</span>\s*</div>',
        html_text,
        flags=re.S,
    )
    day_label = clean_text(day_label_match.group(1)) if day_label_match else f"Day {day_offset}"

    sessions: List[dict] = []

    court_blocks = re.findall(
        r'<button class="accordion-button"[^>]*>\s*<b>(.*?)</b>.*?<tbody>(.*?)</tbody>',
        html_text,
        flags=re.S,
    )

    for court_raw, table_body in court_blocks:
        court_name = clean_text(court_raw)
        session_tour = infer_tour_from_label(court_name)

        rows = re.findall(
            r'<tr>\s*<td class="scheduleInfo"[^>]*>(.*?)</td>\s*</tr>\s*<tr class="scheduledMatch"[^>]*>(.*?)</tr>',
            table_body,
            flags=re.S,
        )

        for time_raw, match_row in rows:
            time_range = clean_text(time_raw)
            participants: List[dict] = []
            seen_ids = set()

            for cell in re.findall(r'<td class="team[12]"[^>]*>(.*?)</td>', match_row, flags=re.S):
                for fragment in extract_training_fragments(cell):
                    player = parse_training_person(fragment, registry)
                    if player and player["id"] not in seen_ids:
                        seen_ids.add(player["id"])
                        participants.append(player)

            if not participants:
                continue

            session_id = slugify(f"{day_offset}-{court_name}-{time_range}-{'-'.join(sorted(seen_ids))}")
            sessions.append(
                {
                    "id": session_id,
                    "dayOffset": day_offset,
                    "dayLabel": day_label,
                    "court": court_name,
                    "timeRange": time_range,
                    "tour": session_tour,
                    "players": participants,
                }
            )

    return day_label, sessions


def parse_player_directory(html_text: str) -> Tuple[str, List[dict]]:
    ranking_date_match = PLAYER_RANKING_DATE_RE.search(html_text)
    ranking_date = ranking_date_match.group(1) if ranking_date_match else ""
    entries: List[dict] = []

    for table_match in PLAYER_TABLE_RE.finditer(html_text):
        tour = table_match.group(1).upper()
        table_html = table_match.group(2)

        for row_html in TABLE_ROW_RE.findall(table_html):
            cells = TABLE_CELL_RE.findall(row_html)
            if len(cells) < 3:
                continue

            ranking_text = clean_text(cells[0])
            if not ranking_text.isdigit():
                continue

            name, ranking_tag = parse_directory_name_and_ranking_tag(cells[1])
            country = normalize_country(cells[2])
            if not name:
                continue

            entries.append(
                {
                    "ranking": int(ranking_text),
                    "name": name,
                    "country": country,
                    "tour": tour,
                    "rankingTag": ranking_tag,
                }
            )

    if not entries:
        raise ValueError("Could not parse ATP/WTA player tables from official player page.")

    return ranking_date, entries


def fetch_official_atp_token() -> str:
    try:
        shell_html = fetch_text(RESULTS_SHELL_URL)
        bundle_match = RESULTS_INDEX_BUNDLE_RE.search(shell_html)
        if not bundle_match:
            raise ValueError("Could not find results index bundle URL.")

        index_bundle_url = urllib.parse.urljoin(RESULTS_SHELL_URL, bundle_match.group(1))
        index_bundle_text = fetch_text(index_bundle_url)

        results_view_match = RESULTS_VIEW_BUNDLE_RE.search(index_bundle_text)
        if not results_view_match:
            raise ValueError("Could not find ResultsView bundle URL.")

        results_view_url = urllib.parse.urljoin(RESULTS_SHELL_URL, f"assets/{results_view_match.group(0)}")
        results_view_text = fetch_text(results_view_url)

        token_match = ATP_TOKEN_RE.search(results_view_text)
        if not token_match:
            raise ValueError("Could not extract ATP bearer token from official results app.")

        return token_match.group(1)
    except Exception as error:
        print(f"Warning: failed to fetch ATP token dynamically, using fallback token: {error}", file=sys.stderr)
        return ATP_FALLBACK_BEARER_TOKEN


def fetch_atp_matches(token: str) -> List[dict]:
    payload = fetch_json(
        RESULTS_BASE_URL,
        extra_headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
    )
    return payload.get("Matches") or []


def fetch_atp_schedule(token: str) -> dict:
    return fetch_json(
        ATP_SCHEDULES_URL,
        extra_headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
    )


def fetch_wta_schedule() -> dict:
    return fetch_json(
        WTA_SCHEDULE_URL,
        extra_headers={
            "apiKey": WTA_SCHEDULE_API_KEY,
        },
    )


def fetch_wta_results_info() -> List[dict]:
    payload = fetch_json(
        WTA_RESULTS_INFO_URL,
        extra_headers={
            "apiKey": WTA_RESULTS_INFO_API_KEY,
        },
    )
    if isinstance(payload, list):
        return payload
    return []


def fetch_atp_draws(token: str) -> dict:
    return fetch_json(
        ATP_DRAWS_URL,
        extra_headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
    )


def fetch_wta_event_draw_rows() -> List[dict]:
    payload = fetch_json(
        WTA_EVENT_DRAWS_URL,
        extra_headers={
            "apiKey": WTA_RESULTS_INFO_API_KEY,
        },
    )
    if isinstance(payload, list):
        return payload
    return []


def parse_atp_draw_singles_rankings(payload: dict) -> Dict[str, int]:
    rankings: Dict[str, int] = {}
    associations = payload.get("Associations") or []

    for association in associations:
        events = association.get("Events") or []
        for event in events:
            event_code = str(event.get("EventTypeCode") or "").strip().upper()
            if event_code not in {"MS", "QS"}:
                continue

            for round_item in event.get("Rounds") or []:
                for fixture in round_item.get("Fixtures") or []:
                    for side in ("DrawLineTop", "DrawLineBottom"):
                        draw_line = fixture.get(side) or {}
                        rank = parse_int(draw_line.get("SeedingRank"))
                        if rank is None or rank <= 0:
                            continue

                        for draw_player in draw_line.get("Players") or []:
                            atp_player_id = normalize_atp_player_id(draw_player.get("PlayerId"))
                            if not atp_player_id:
                                continue

                            current = rankings.get(atp_player_id)
                            if current is None or rank < current:
                                rankings[atp_player_id] = rank

    return rankings


def enrich_players_with_atp_draw_ids(registry: Dict[str, dict], payload: dict) -> int:
    applied = 0
    associations = payload.get("Associations") or []

    for association in associations:
        events = association.get("Events") or []
        for event in events:
            event_code = str(event.get("EventTypeCode") or "").strip().upper()
            if event_code not in {"MS", "MD", "QS", "QD"}:
                continue

            for round_item in event.get("Rounds") or []:
                for fixture in round_item.get("Fixtures") or []:
                    for side in ("DrawLineTop", "DrawLineBottom"):
                        draw_line = fixture.get(side) or {}
                        for draw_player in draw_line.get("Players") or []:
                            atp_player_id = normalize_atp_player_id(draw_player.get("PlayerId"))
                            if not atp_player_id:
                                continue

                            name = extract_atp_draw_player_name(draw_player)
                            country = extract_atp_draw_player_country(draw_player)
                            if not name:
                                continue

                            player = find_existing_player(registry, name, country)
                            if not player:
                                player = find_existing_player_approx(registry, name, country)
                            if not player:
                                player = upsert_player(registry, name, country)
                            if not player:
                                continue

                            changed = False
                            if country and not str(player.get("country") or "").strip():
                                player["country"] = country
                                changed = True
                            if not str(player.get("tour") or "").strip():
                                player["tour"] = "ATP"
                                changed = True
                            if attach_player_ids(player, atp_player_id=atp_player_id):
                                changed = True

                            if changed:
                                applied += 1

    return applied


def atp_draw_round_code(round_item: dict) -> str:
    round_name = str(round_item.get("RoundName") or "").strip().lower()
    if "qualifying round" in round_name:
        number_match = re.search(r"(\d+)", round_name)
        return f"Q{number_match.group(1)}" if number_match else "Q"
    if round_name == "final":
        return "F"
    if round_name == "semifinal":
        return "SF"
    if round_name == "quarterfinal":
        return "QF"
    round_match = re.search(r"round of\s+(\d+)", round_name)
    if round_match:
        return f"R{round_match.group(1)}"

    modernized = parse_int(round_item.get("RoundIdModernized"))
    if modernized is not None:
        return {
            7: "F",
            6: "SF",
            5: "QF",
            4: "R16",
            3: "R32",
            2: "R64",
            1: "R128",
            -30: "Q1",
            -29: "Q2",
            -28: "Q3",
        }.get(modernized, str(modernized))

    round_id = parse_int(round_item.get("RoundId"))
    return f"R{round_id}" if round_id is not None else "-"


def extract_atp_draw_line_players(draw_line: dict, registry: Dict[str, dict], side: str) -> List[dict]:
    players: List[dict] = []

    for draw_player in (draw_line or {}).get("Players") or []:
        atp_player_id = normalize_atp_player_id(draw_player.get("PlayerId"))
        name = extract_atp_draw_player_name(draw_player)
        country = extract_atp_draw_player_country(draw_player)
        if not name or name.lower() == "bye":
            continue

        player = find_player_by_atp_id(registry, atp_player_id)
        if not player:
            player = find_existing_player(registry, name, country)
        if not player:
            player = find_existing_player_approx(registry, name, country)
        if not player:
            player = upsert_player(registry, name, country)
        if not player:
            continue

        if country and not str(player.get("country") or "").strip():
            player["country"] = country
        player["tour"] = player.get("tour") or "ATP"
        attach_player_ids(player, atp_player_id=atp_player_id)

        snapshot = {
            "id": player["id"],
            "name": player.get("name", name),
            "country": player.get("country", country),
            "tour": "ATP",
            "side": side,
        }
        if player.get("atpPlayerId"):
            snapshot["atpPlayerId"] = player["atpPlayerId"]
        players.append(snapshot)

    return players


def parse_atp_doubles_draw_matches(payload: dict, registry: Dict[str, dict]) -> List[dict]:
    parsed: List[dict] = []

    for association in payload.get("Associations") or []:
        for event in association.get("Events") or []:
            event_code = str(event.get("EventTypeCode") or "").strip().upper()
            if event_code not in {"MD", "QD"}:
                continue

            for round_item in event.get("Rounds") or []:
                round_code = atp_draw_round_code(round_item)
                for index, fixture in enumerate(round_item.get("Fixtures") or [], start=1):
                    side_a = extract_atp_draw_line_players(fixture.get("DrawLineTop") or {}, registry, "A")
                    side_b = extract_atp_draw_line_players(fixture.get("DrawLineBottom") or {}, registry, "B")
                    if not side_a or not side_b:
                        continue

                    match_code = str(fixture.get("MatchCode") or "").strip()
                    result = str(fixture.get("ResultString") or "").strip()
                    status = "F" if result else "U"
                    parsed.append(
                        {
                            "id": f"ATP-{match_code}" if match_code else f"ATP-DRAW-{event_code}-{round_code}-{index}",
                            "startTime": "",
                            "status": status,
                            "round": round_code,
                            "roundCode": round_code,
                            "roundLabel": format_round_label(event_code, round_code),
                            "draw": event_code,
                            "discipline": "doubles",
                            "tour": "ATP",
                            "court": "",
                            "score": result,
                            "result": result,
                            "source": "atpDraw",
                            "players": side_a + side_b,
                        }
                    )

    return dedupe_matches_by_id(parsed)


def xml_local_name(tag: str) -> str:
    return str(tag or "").split("}", 1)[-1]


def extract_draw_line_rank_from_xml_text(block_text: str) -> Optional[int]:
    for tag_name in ("SeedingRank", "PlayerSinglesRank", "SinglesRank", "PlayerRank", "Ranking", "Rank"):
        match = re.search(
            rf"<(?:[A-Za-z0-9_]+:)?{tag_name}>\s*([^<]+)\s*</(?:[A-Za-z0-9_]+:)?{tag_name}>",
            block_text,
            flags=re.I,
        )
        if not match:
            continue
        rank, _ = parse_ranking_hint(match.group(1))
        if rank is not None and rank > 0:
            return rank
    return None


def parse_wta_draw_xml_singles_rankings(xml_text: str) -> Dict[str, int]:
    rankings: Dict[str, int] = {}

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return rankings

    for event in root.iter():
        if xml_local_name(event.tag) != "Event":
            continue

        event_code = ""
        for child in event:
            if xml_local_name(child.tag) == "EventTypeCode":
                event_code = str(child.text or "").strip().upper()
                break
        if event_code not in {"LS", "RS"}:
            continue

        for draw_line in event.iter():
            local_name = xml_local_name(draw_line.tag)
            if local_name != "DrawLine":
                continue

            rank = None
            for child in draw_line:
                if xml_local_name(child.tag) == "SeedingRank":
                    rank = parse_int(child.text)
                    break
            if rank is None or rank <= 0:
                continue

            for candidate in draw_line.iter():
                if xml_local_name(candidate.tag) != "PlayerId":
                    continue

                wta_player_id = normalize_wta_player_id(candidate.text)
                if not wta_player_id:
                    continue

                current = rankings.get(wta_player_id)
                if current is None or rank < current:
                    rankings[wta_player_id] = rank

    for event_block in WTA_XML_EVENT_BLOCK_RE.findall(xml_text):
        type_match = WTA_XML_EVENT_TYPE_RE.search(event_block)
        event_code = str(type_match.group(1) if type_match else "").strip().upper()
        if event_code not in {"LS", "RS"}:
            continue

        for draw_line_block in WTA_XML_DRAW_LINE_RE.findall(event_block):
            rank = extract_draw_line_rank_from_xml_text(draw_line_block)
            if rank is None or rank <= 0:
                continue

            for player_id_text in WTA_XML_PLAYER_ID_RE.findall(draw_line_block):
                wta_player_id = normalize_wta_player_id(player_id_text)
                if not wta_player_id:
                    continue

                current = rankings.get(wta_player_id)
                if current is None or rank < current:
                    rankings[wta_player_id] = rank

    return rankings


def parse_wta_event_draw_singles_rankings(rows: List[dict]) -> Dict[str, int]:
    merged: Dict[str, int] = {}

    for row in rows:
        xml_text = str(row.get("drawxml") or "").strip()
        if not xml_text:
            continue

        extracted = parse_wta_draw_xml_singles_rankings(xml_text)
        for player_id, rank in extracted.items():
            current = merged.get(player_id)
            if current is None or rank < current:
                merged[player_id] = rank

    return merged


def child_text_by_local_name(node: ET.Element, target_name: str) -> str:
    for child in node:
        if xml_local_name(child.tag) == target_name:
            return str(child.text or "").strip()
    return ""


def normalize_entry_type(value: object) -> str:
    return re.sub(r"[^A-Z]", "", str(value or "").strip().upper())


def find_player_by_initial_and_lastname(registry: Dict[str, dict], display_name: str, country: str) -> Optional[dict]:
    text = SPACE_RE.sub(" ", str(display_name or "").strip())
    country_code = str(country or "").strip().upper()
    match = re.match(r"^([A-Za-z])[.\s]+([A-Za-zÀ-ÖØ-öø-ÿ'` -]+)$", text)
    if not match:
        return None

    first_initial = match.group(1).lower()
    last_name = SPACE_RE.sub(" ", match.group(2)).strip().lower()
    if not last_name:
        return None

    candidates = []
    for player in registry.values():
        name = str(player.get("name") or "").strip()
        if not name:
            continue

        parts = [part for part in name.split(" ") if part]
        if not parts:
            continue

        player_last = parts[-1].lower()
        player_first_initial = parts[0][0].lower()
        if player_last != last_name or player_first_initial != first_initial:
            continue

        player_country = str(player.get("country") or "").strip().upper()
        if country_code and player_country and player_country != country_code:
            continue

        candidates.append(player)

    if len(candidates) == 1:
        return candidates[0]
    return None


def enrich_players_with_wta_draw_ids(registry: Dict[str, dict], rows: List[dict]) -> int:
    applied = 0

    for row in rows:
        xml_text = str(row.get("drawxml") or "").strip()
        if not xml_text:
            continue

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            continue

        for event in root.iter():
            if xml_local_name(event.tag) != "Event":
                continue

            event_code = child_text_by_local_name(event, "EventTypeCode").upper()
            if event_code not in {"LS", "LD", "RS"}:
                continue

            for draw_line in event.iter():
                if xml_local_name(draw_line.tag) != "DrawLine":
                    continue

                entry_type = normalize_entry_type(child_text_by_local_name(draw_line, "EntryType"))

                for player_node in draw_line.iter():
                    if xml_local_name(player_node.tag) != "Player":
                        continue

                    wta_player_id = normalize_wta_player_id(
                        player_node.get("id") or child_text_by_local_name(player_node, "PlayerId")
                    )
                    if not wta_player_id:
                        continue

                    first_name = child_text_by_local_name(player_node, "FirstName")
                    last_name = child_text_by_local_name(player_node, "LastName") or child_text_by_local_name(player_node, "SurName")
                    display_name = child_text_by_local_name(player_node, "DisplayLine")
                    if not display_name:
                        display_name = child_text_by_local_name(player_node, "PlayerDisplayLine")
                    country = child_text_by_local_name(player_node, "Nationality") or child_text_by_local_name(player_node, "Country")
                    full_name = split_name(first_name, last_name)

                    target_player = None
                    if full_name:
                        target_player = find_existing_player(registry, full_name, country)
                        if not target_player:
                            target_player = find_existing_player_approx(registry, full_name, country)
                    if not target_player and display_name:
                        target_player = find_player_by_initial_and_lastname(registry, display_name, country)
                    if not target_player:
                        continue

                    changed = False
                    if attach_player_ids(target_player, wta_player_id=wta_player_id):
                        changed = True
                    if not str(target_player.get("tour") or "").strip():
                        target_player["tour"] = "WTA"
                        changed = True
                    if event_code == "LS" and entry_type:
                        if target_player.get("singlesEntryType") != entry_type:
                            target_player["singlesEntryType"] = entry_type
                            changed = True
                    if changed:
                        applied += 1

    return applied


def extract_wta_draw_line_players(draw_line: ET.Element, registry: Dict[str, dict], side: str) -> List[dict]:
    players: List[dict] = []

    for player_node in draw_line.iter():
        if xml_local_name(player_node.tag) != "Player":
            continue

        wta_player_id = normalize_wta_player_id(
            player_node.get("id") or child_text_by_local_name(player_node, "PlayerId")
        )
        if wta_player_id == "0":
            continue

        first_name = child_text_by_local_name(player_node, "FirstName")
        last_name = child_text_by_local_name(player_node, "LastName") or child_text_by_local_name(player_node, "SurName")
        display_name = child_text_by_local_name(player_node, "DisplayLine") or child_text_by_local_name(player_node, "PlayerDisplayLine")
        country = child_text_by_local_name(player_node, "Nationality") or child_text_by_local_name(player_node, "Country")
        full_name = split_name(first_name, last_name)
        if not full_name and display_name:
            full_name = normalize_person_name(display_name)
        if not full_name or full_name.lower() == "bye":
            continue

        player = find_existing_player(registry, full_name, country)
        if not player:
            player = find_existing_player_approx(registry, full_name, country)
        if not player:
            player = upsert_player(registry, full_name, country)
        if not player:
            continue

        attach_player_ids(player, wta_player_id=wta_player_id)
        player["tour"] = player.get("tour") or "WTA"
        snapshot = {
            "id": player["id"],
            "name": player.get("name", full_name),
            "country": player.get("country", country),
            "tour": "WTA",
            "side": side,
        }
        if player.get("wtaPlayerId"):
            snapshot["wtaPlayerId"] = player["wtaPlayerId"]
        players.append(snapshot)

    return players


def wta_draw_round_code(draw_size: int) -> str:
    if draw_size >= 128:
        return "R128"
    if draw_size >= 64:
        return "R64"
    if draw_size >= 32:
        return "R32"
    if draw_size >= 16:
        return "R16"
    return "R1"


def parse_wta_doubles_draw_matches(rows: List[dict], registry: Dict[str, dict]) -> List[dict]:
    parsed: List[dict] = []

    for row in rows:
        xml_text = str(row.get("drawxml") or row.get("DrawXml") or row.get("DRAWXML") or "").strip()
        if not xml_text:
            continue

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            continue

        for event in root.iter():
            if xml_local_name(event.tag) != "Event":
                continue

            event_code = child_text_by_local_name(event, "EventTypeCode").upper()
            if event_code != "LD":
                continue

            draw_size = parse_int(child_text_by_local_name(event, "DrawSize")) or 32
            round_code = wta_draw_round_code(draw_size)
            draw_node = next((child for child in event if xml_local_name(child.tag) == "Draw"), None)
            if draw_node is None:
                continue

            draw_lines = [
                draw_line
                for draw_line in draw_node
                if xml_local_name(draw_line.tag) == "DrawLine"
            ]
            draw_lines.sort(key=lambda node: parse_int(node.get("Pos")) or 0)

            for index in range(0, len(draw_lines), 2):
                try:
                    top_line = draw_lines[index]
                    bottom_line = draw_lines[index + 1]
                except IndexError:
                    continue

                top_pos = parse_int(top_line.get("Pos")) or (index + 1)
                bottom_pos = parse_int(bottom_line.get("Pos")) or (index + 2)
                side_a = extract_wta_draw_line_players(top_line, registry, "A")
                side_b = extract_wta_draw_line_players(bottom_line, registry, "B")
                if not side_a or not side_b:
                    continue

                parsed.append(
                    {
                        "id": f"WTA-DRAW-LD-{round_code}-{top_pos}-{bottom_pos}",
                        "startTime": "",
                        "status": "U",
                        "round": round_code,
                        "roundCode": round_code,
                        "roundLabel": format_round_label("MD", round_code),
                        "draw": "MD",
                        "discipline": "doubles",
                        "tour": "WTA",
                        "court": "",
                        "score": "",
                        "result": "",
                        "source": "wtaDraw",
                        "players": side_a + side_b,
                    }
                )

    return parsed


def match_roster_signature(match: dict) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    side_a = sorted(
        str(player.get("id") or "").strip()
        for player in match.get("players") or []
        if str(player.get("side") or "").upper() == "A" and str(player.get("id") or "").strip()
    )
    side_b = sorted(
        str(player.get("id") or "").strip()
        for player in match.get("players") or []
        if str(player.get("side") or "").upper() == "B" and str(player.get("id") or "").strip()
    )
    sides = sorted([tuple(side_a), tuple(side_b)])
    return sides[0], sides[1]


def merge_draw_fallback_matches(matches: List[dict], fallback_matches: List[dict]) -> int:
    existing = {
        match_roster_signature(match)
        for match in matches
        if str(match.get("discipline") or "").lower() == "doubles"
        and match_roster_signature(match) != (tuple(), tuple())
    }

    added = 0
    for match in fallback_matches:
        signature = match_roster_signature(match)
        if signature == (tuple(), tuple()) or signature in existing:
            continue
        matches.append(match)
        existing.add(signature)
        added += 1

    return added


def fetch_atp_official_rankings_report_entries(discipline: str = "singles") -> List[dict]:
    normalized_discipline = normalize_ranking_discipline(discipline)
    report_url = (
        ATP_OFFICIAL_DOUBLES_RANKINGS_REPORT_URL
        if normalized_discipline == "doubles"
        else ATP_OFFICIAL_SINGLES_RANKINGS_REPORT_URL
    )
    report_text = extract_pdf_text(fetch_bytes(report_url))
    entries: List[dict] = []

    for row in parse_atp_ranking_report_rows(report_text):
        entries.append(
            {
                "name": row["name"],
                "country": row.get("country", ""),
                "ranking": row["ranking"],
                "tour": "ATP",
                "rankingTag": "",
                "rankingDiscipline": normalized_discipline,
            }
        )

    return entries


def fetch_atp_official_rankings_entries(registry: Dict[str, dict], discipline: str = "singles") -> List[dict]:
    merged: Dict[str, dict] = {}
    normalized_discipline = normalize_ranking_discipline(discipline)

    try:
        report_entries = fetch_atp_official_rankings_report_entries(normalized_discipline)
        if report_entries:
            return report_entries
    except Exception as error:
        print(f"Warning: failed to fetch ATP official {normalized_discipline} rankings report: {error}", file=sys.stderr)

    url_template = (
        ATP_OFFICIAL_DOUBLES_RANKINGS_URL_TEMPLATE
        if normalized_discipline == "doubles"
        else ATP_OFFICIAL_RANKINGS_URL_TEMPLATE
    )

    for rank_range in ATP_OFFICIAL_RANK_RANGE_VALUES:
        url = url_template.format(rank_range=urllib.parse.quote_plus(rank_range))
        try:
            html_text = fetch_text(url)
            rows = parse_atp_official_ranking_rows(html_text)
            for row in rows:
                player = resolve_atp_ranking_row_to_player(registry, row)
                if not player:
                    continue

                entry = {
                    "name": player.get("name", ""),
                    "country": player.get("country", ""),
                    "ranking": row["ranking"],
                    "tour": "ATP",
                    "rankingTag": "",
                    "rankingDiscipline": normalized_discipline,
                    "atpPlayerId": row.get("atpPlayerId", ""),
                }
                key = entry["name"]
                current = merged.get(key)
                if current is None or entry["ranking"] < current["ranking"]:
                    merged[key] = entry
        except Exception as error:
            print(f"Warning: failed to fetch ATP official {normalized_discipline} rankings range {rank_range}: {error}", file=sys.stderr)

    return list(merged.values())


def fetch_wta_official_rankings_entries(
    base_url: str = WTA_OFFICIAL_RANKINGS_URL,
    discipline: str = "singles",
) -> List[dict]:
    merged: Dict[Tuple[str, str], dict] = {}
    last_signature: Tuple[Tuple[str, str, int], ...] = tuple()
    normalized_discipline = normalize_ranking_discipline(discipline)

    for page in range(1, 31):
        if page == 1:
            url = base_url
        else:
            separator = "&" if "?" in base_url else "?"
            url = f"{base_url}{separator}page={page}"

        html_text = fetch_text(url)
        rows = parse_wta_official_rankings(html_text)
        if not rows:
            if page > 1:
                break
            continue

        signature = tuple((row.get("name", ""), row.get("country", ""), int(row.get("ranking") or 0)) for row in rows[:20])
        if page > 1 and signature == last_signature:
            break
        last_signature = signature

        for row in rows:
            key = (str(row.get("name") or "").strip().lower(), str(row.get("country") or "").strip().upper())
            current = merged.get(key)
            rank = parse_int(row.get("ranking"))
            if rank is None or rank <= 0:
                continue

            if current is None or rank < int(current.get("ranking") or 10**9):
                merged[key] = {
                    "name": row.get("name", ""),
                    "country": row.get("country", ""),
                    "ranking": rank,
                    "tour": "WTA",
                    "rankingTag": "",
                    "rankingDiscipline": normalized_discipline,
                    "wtaPlayerId": row.get("wtaPlayerId", ""),
                }

    return list(merged.values())


def fetch_wta_official_profile_entries(base_url: str) -> List[dict]:
    merged: Dict[Tuple[str, str], dict] = {}
    last_signature: Tuple[Tuple[str, str], ...] = tuple()

    for page in range(1, 31):
        if page == 1:
            url = base_url
        else:
            separator = "&" if "?" in base_url else "?"
            url = f"{base_url}{separator}page={page}"

        html_text = fetch_text(url)
        rows = parse_wta_official_profile_entries(html_text)
        if not rows:
            if page > 1:
                break
            continue

        signature = tuple((row.get("name", ""), row.get("wtaPlayerId", "")) for row in rows[:20])
        if page > 1 and signature == last_signature:
            break
        last_signature = signature

        for row in rows:
            token_key = name_token_key(row.get("name", ""))
            player_id = normalize_wta_player_id(row.get("wtaPlayerId"))
            if not token_key or not player_id:
                continue

            key = (" ".join(token_key), player_id)
            merged[key] = {
                "name": row.get("name", ""),
                "country": row.get("country", ""),
                "tour": "WTA",
                "rankingTag": "",
                "wtaPlayerId": player_id,
            }

    return list(merged.values())


def enrich_players_from_wta_results_info(registry: Dict[str, dict], rows: List[dict]) -> int:
    applied = 0

    for row in rows:
        allow_ranking = is_wta_singles_row(row)
        for side in ("A", "A2", "B", "B2"):
            name = split_name(row.get(f"PlayerNameFirst{side}", ""), row.get(f"PlayerNameLast{side}", ""))
            country = row.get(f"PlayerCountry{side}", "")
            player = find_existing_player(registry, name, country)
            if not player:
                player = find_existing_player_approx(registry, name, country)
            if not player:
                player = upsert_player(registry, name, country)
            if not player:
                continue

            if allow_ranking:
                changed = apply_ranking_hint(
                    player,
                    extract_wta_ranking_value(row, side),
                    extract_wta_ranking_tag(row, side),
                )
                if changed:
                    applied += 1

            player["tour"] = player.get("tour") or "WTA"

    return applied


def enrich_players_from_draw_rankings(
    registry: Dict[str, dict],
    atp_ranking_by_player_id: Dict[str, int],
    wta_ranking_by_player_id: Dict[str, int],
) -> int:
    applied = 0

    for player in registry.values():
        if player.get("ranking") not in (None, ""):
            continue

        tour = str(player.get("tour") or "").strip().upper()
        atp_player_id = normalize_atp_player_id(player.get("atpPlayerId"))
        wta_player_id = normalize_wta_player_id(player.get("wtaPlayerId"))

        ranking: Optional[int] = None
        inferred_tour = ""

        if tour == "ATP" and atp_player_id:
            ranking = atp_ranking_by_player_id.get(atp_player_id)
            inferred_tour = "ATP"
        elif tour == "WTA" and wta_player_id:
            ranking = wta_ranking_by_player_id.get(wta_player_id)
            inferred_tour = "WTA"
        elif atp_player_id and atp_player_id in atp_ranking_by_player_id:
            ranking = atp_ranking_by_player_id[atp_player_id]
            inferred_tour = "ATP"
        elif wta_player_id and wta_player_id in wta_ranking_by_player_id:
            ranking = wta_ranking_by_player_id[wta_player_id]
            inferred_tour = "WTA"

        if ranking is None:
            continue

        set_player_ranking(player, ranking, "", "singles")
        if inferred_tour and not str(player.get("tour") or "").strip():
            player["tour"] = inferred_tour
        applied += 1

    return applied


def enrich_wta_rankings_from_profile_pages(registry: Dict[str, dict], matches: List[dict]) -> int:
    applied = 0
    profile_rank_cache: Dict[str, Dict[str, Optional[int]]] = {}

    candidates = [
        player
        for player in registry.values()
        if normalize_wta_player_id(player.get("wtaPlayerId"))
        and str(player.get("tour") or "").strip().upper() in {"", "WTA"}
        and (
            player.get("singlesRanking") in (None, "")
            or player.get("doublesRanking") in (None, "")
            or player.get("ranking") in (None, "")
        )
    ]

    for player in sorted(candidates, key=lambda item: str(item.get("name") or "").lower()):
        wta_player_id = normalize_wta_player_id(player.get("wtaPlayerId"))
        if not wta_player_id:
            continue

        if wta_player_id not in profile_rank_cache:
            profile_rank_cache[wta_player_id] = fetch_wta_profile_rankings(
                wta_player_id,
                str(player.get("name") or ""),
            )
        rankings = profile_rank_cache[wta_player_id]
        changed = False

        if player.get("singlesRanking") in (None, "") and rankings.get("singles") is not None:
            changed = set_player_ranking(player, rankings["singles"], "", "singles") or changed
        if player.get("doublesRanking") in (None, "") and rankings.get("doubles") is not None:
            changed = set_player_ranking(player, rankings["doubles"], "", "doubles") or changed
        if not changed:
            continue

        if not str(player.get("tour") or "").strip():
            player["tour"] = "WTA"
        applied += 1

    return applied


def enrich_atp_rankings_from_profile_pages(registry: Dict[str, dict], matches: List[dict]) -> int:
    applied = 0
    profile_rank_cache: Dict[str, Dict[str, Optional[int]]] = {}
    candidate_ids = {
        normalize_atp_player_id(player.get("atpPlayerId"))
        for match in matches
        for player in match.get("players", [])
        if str(player.get("tour") or "").strip().upper() == "ATP"
    }
    candidate_ids.discard("")

    candidates = [
        player
        for player in registry.values()
        if normalize_atp_player_id(player.get("atpPlayerId")) in candidate_ids
        and str(player.get("tour") or "").strip().upper() in {"", "ATP"}
    ]

    for player in sorted(candidates, key=lambda item: str(item.get("name") or "").lower()):
        atp_player_id = normalize_atp_player_id(player.get("atpPlayerId"))
        if not atp_player_id:
            continue

        if atp_player_id not in profile_rank_cache:
            profile_rank_cache[atp_player_id] = fetch_atp_profile_rankings(atp_player_id)
        rankings = profile_rank_cache[atp_player_id]
        changed = False

        if rankings.get("singles") is not None:
            changed = set_player_ranking(player, rankings["singles"], "", "singles", replace=True) or changed
        if rankings.get("doubles") is not None:
            changed = set_player_ranking(player, rankings["doubles"], "", "doubles", replace=True) or changed
        if not changed:
            continue

        if not str(player.get("tour") or "").strip():
            player["tour"] = "ATP"
        applied += 1

    return applied


def enrich_players_from_official_rankings(registry: Dict[str, dict], entries: List[dict]) -> int:
    applied = 0

    for entry in entries:
        player = find_existing_player(registry, entry["name"], entry.get("country", ""))
        if not player:
            player = find_existing_player_approx(registry, entry["name"], entry.get("country", ""))
        if not player:
            continue

        changed = False
        if attach_player_ids(
            player,
            atp_player_id=entry.get("atpPlayerId", ""),
            wta_player_id=entry.get("wtaPlayerId", ""),
        ):
            changed = True
        official_name = normalize_person_name(str(entry.get("name") or ""))
        if official_name and name_token_key(official_name) == name_token_key(player.get("name", "")):
            if player.get("name") != official_name:
                player["name"] = official_name
                changed = True
        rank = parse_int(entry.get("ranking"))
        if rank is not None:
            changed = set_player_ranking(
                player,
                rank,
                str(entry.get("rankingTag") or ""),
                str(entry.get("rankingDiscipline") or "singles"),
                replace=True,
            ) or changed
        if not str(player.get("tour") or "").strip() and str(entry.get("tour") or "").strip():
            player["tour"] = entry["tour"]
            changed = True

        if changed:
            applied += 1

    return applied


def remove_doubles_rankings(registry: Dict[str, dict]) -> int:
    return 0


def enrich_players_from_directory(registry: Dict[str, dict], entries: List[dict]) -> int:
    matched = 0

    for entry in entries:
        matched_exact = True
        player = find_existing_player(registry, entry["name"], entry["country"])
        if not player:
            matched_exact = False
            player = find_existing_player_approx(registry, entry["name"], entry["country"])
        if not player:
            continue

        if matched_exact and entry["name"]:
            player["name"] = entry["name"]
        if entry["country"]:
            player["country"] = entry["country"]
        if entry["tour"] == "ATP":
            player["singlesEntryRanking"] = entry["ranking"]
            if entry.get("rankingTag"):
                player["singlesEntryRankingTag"] = entry["rankingTag"]
        else:
            set_player_ranking(player, entry["ranking"], entry.get("rankingTag", ""), "singles")
        player["tour"] = entry["tour"]
        matched += 1

    return matched


def infer_match_tour(match: dict) -> str:
    match_id = str(match.get("id") or "").strip()
    if match_id.startswith("ATP-"):
        return "ATP"
    if match_id:
        return "WTA"
    return ""


def enrich_players_with_match_tour(registry: Dict[str, dict], matches: List[dict]) -> int:
    tours_by_player: Dict[str, set] = {}

    for match in matches:
        tour = infer_match_tour(match)
        if not tour:
            continue

        for player in match.get("players") or []:
            player_id = str(player.get("id") or "").strip()
            if not player_id:
                continue
            tours_by_player.setdefault(player_id, set()).add(tour)

    inferred = 0

    for player_id, tours in tours_by_player.items():
        if len(tours) != 1:
            continue

        player = registry.get(player_id)
        if not player:
            continue
        if str(player.get("tour") or "").strip():
            continue

        player["tour"] = next(iter(tours))
        inferred += 1

    return inferred


def sync_player_snapshots(items: List[dict], registry: Dict[str, dict]) -> None:
    for item in items:
        updated_players: List[dict] = []
        for player in item.get("players") or []:
            player_id = player.get("id")
            canonical = registry.get(player_id or "")
            snapshot = {
                "id": player_id,
                "name": (canonical or {}).get("name") or player.get("name", ""),
                "country": (canonical or {}).get("country") or player.get("country", ""),
            }

            if "side" in player:
                snapshot["side"] = player["side"]
            if canonical and canonical.get("ranking") is not None:
                snapshot["ranking"] = canonical["ranking"]
            if canonical and canonical.get("rankingTag"):
                snapshot["rankingTag"] = canonical["rankingTag"]
            for field in ("singlesRanking", "singlesRankingTag", "doublesRanking", "doublesRankingTag"):
                if canonical and canonical.get(field) not in (None, ""):
                    snapshot[field] = canonical[field]
            if canonical and canonical.get("tour"):
                snapshot["tour"] = canonical["tour"]
            if canonical and canonical.get("atpPlayerId"):
                snapshot["atpPlayerId"] = canonical["atpPlayerId"]
            if canonical and canonical.get("wtaPlayerId"):
                snapshot["wtaPlayerId"] = canonical["wtaPlayerId"]
            if canonical and canonical.get("singlesEntryType"):
                snapshot["singlesEntryType"] = canonical["singlesEntryType"]

            updated_players.append(snapshot)

        item["players"] = updated_players


def build_output() -> dict:
    registry: Dict[str, dict] = {}
    atp_token = fetch_official_atp_token()

    wta_matches_payload = fetch_json(MATCHES_URL)
    wta_matches = parse_matches(wta_matches_payload, registry)

    atp_matches_payload = {"Matches": fetch_atp_matches(atp_token)}
    atp_matches = parse_atp_matches(atp_matches_payload, registry)
    matches = wta_matches + atp_matches

    atp_schedule_map = parse_atp_schedule(fetch_atp_schedule(atp_token))
    wta_schedule_map = parse_wta_schedule(fetch_wta_schedule())
    merge_schedule_into_matches(matches, {**atp_schedule_map, **wta_schedule_map})

    training_sessions: List[dict] = []
    training_days = []

    for day_offset in (0, 1):
        html_text = fetch_text(TRAINING_URL_TEMPLATE.format(day=day_offset))
        day_label, day_sessions = parse_training_day(html_text, day_offset, registry)
        training_days.append({"dayOffset": day_offset, "label": day_label})
        training_sessions.extend(day_sessions)

    players_html = fetch_text(PLAYERS_URL)
    ranking_date, directory_entries = parse_player_directory(players_html)
    enrich_players_from_directory(registry, directory_entries)
    apply_player_id_overrides(registry)

    try:
        atp_official_entries = fetch_atp_official_rankings_entries(registry, "singles")
        enrich_players_from_official_rankings(registry, atp_official_entries)
    except Exception as error:
        print(f"Warning: failed to enrich rankings from ATP official rankings page: {error}", file=sys.stderr)

    try:
        atp_official_doubles_entries = fetch_atp_official_rankings_entries(registry, "doubles")
        enrich_players_from_official_rankings(registry, atp_official_doubles_entries)
    except Exception as error:
        print(f"Warning: failed to enrich rankings from ATP official doubles rankings page: {error}", file=sys.stderr)

    try:
        enrich_atp_rankings_from_profile_pages(registry, matches)
    except Exception as error:
        print(f"Warning: failed to enrich rankings from ATP profile pages: {error}", file=sys.stderr)

    atp_draw_payload: dict = {}
    atp_draw_rankings: Dict[str, int] = {}
    atp_draw_fallback_count = 0
    try:
        atp_draw_payload = fetch_atp_draws(atp_token)
        enrich_players_with_atp_draw_ids(registry, atp_draw_payload)
        atp_draw_fallback_count = merge_draw_fallback_matches(
            matches,
            parse_atp_doubles_draw_matches(atp_draw_payload, registry),
        )
        atp_draw_rankings = parse_atp_draw_singles_rankings(atp_draw_payload)
    except Exception as error:
        print(f"Warning: failed to enrich rankings from ATP draws API: {error}", file=sys.stderr)

    wta_draw_rankings: Dict[str, int] = {}
    wta_draw_fallback_count = 0
    try:
        wta_event_draw_rows = fetch_wta_event_draw_rows()
        enrich_players_with_wta_draw_ids(registry, wta_event_draw_rows)
        wta_draw_fallback_count = merge_draw_fallback_matches(
            matches,
            parse_wta_doubles_draw_matches(wta_event_draw_rows, registry),
        )
        wta_draw_rankings = parse_wta_event_draw_singles_rankings(wta_event_draw_rows)
    except Exception as error:
        print(f"Warning: failed to enrich rankings from WTA draw XML API: {error}", file=sys.stderr)

    wta_results_info_rows: List[dict] = []
    try:
        wta_results_info_rows = fetch_wta_results_info()
        enrich_players_from_wta_results_info(registry, wta_results_info_rows)
    except Exception as error:
        print(f"Warning: failed to enrich rankings from WTA results info API: {error}", file=sys.stderr)

    try:
        wta_official_entries = fetch_wta_official_rankings_entries(WTA_OFFICIAL_RANKINGS_URL, "singles")
        enrich_players_from_official_rankings(registry, wta_official_entries)
    except Exception as error:
        print(f"Warning: failed to enrich rankings from WTA official rankings page: {error}", file=sys.stderr)

    try:
        wta_doubles_rankings_entries = fetch_wta_official_rankings_entries(WTA_OFFICIAL_DOUBLES_URL, "doubles")
        enrich_players_from_official_rankings(registry, wta_doubles_rankings_entries)
        wta_doubles_profile_entries = fetch_wta_official_profile_entries(WTA_OFFICIAL_DOUBLES_URL)
        enrich_players_from_official_rankings(registry, wta_doubles_profile_entries)
    except Exception as error:
        print(f"Warning: failed to enrich profile ids from WTA official doubles rankings page: {error}", file=sys.stderr)

    enrich_players_from_draw_rankings(registry, atp_draw_rankings, wta_draw_rankings)
    apply_atp_ranking_overrides(registry)
    remove_doubles_rankings(registry)
    enrich_players_with_match_tour(registry, matches)
    alias_map = merge_duplicate_player_variants(registry)
    remap_player_snapshots(matches, alias_map, registry)
    remap_player_snapshots(training_sessions, alias_map, registry)
    enrich_players_from_training_sessions(registry, training_sessions)
    try:
        enrich_wta_rankings_from_profile_pages(registry, matches)
    except Exception as error:
        print(f"Warning: failed to enrich rankings from WTA profile pages: {error}", file=sys.stderr)
    sync_player_snapshots(matches, registry)
    sync_player_snapshots(training_sessions, registry)

    players = sorted(registry.values(), key=lambda p: (p.get("name") or "").lower())
    doubles_matches = [match for match in matches if str(match.get("discipline") or "").lower() == "doubles"]
    doubles_player_ids = {
        str(player.get("id") or "").strip()
        for match in doubles_matches
        for player in match.get("players", [])
        if str(player.get("id") or "").strip()
    }

    return {
        "metadata": {
            "tournament": "Mutua Madrid Open",
            "season": 2026,
            "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "playerRankingDate": ranking_date,
            "sources": {
                "matches": {
                    "wta": MATCHES_URL,
                    "wtaResultsInfo": WTA_RESULTS_INFO_URL,
                    "atp": RESULTS_BASE_URL,
                },
                "schedules": {
                    "wta": WTA_SCHEDULE_URL,
                    "atp": ATP_SCHEDULES_URL,
                },
                "draws": {
                    "wta": WTA_EVENT_DRAWS_URL,
                    "atp": ATP_DRAWS_URL,
                },
                "rankings": {
                    "atpSingles": ATP_OFFICIAL_SINGLES_RANKINGS_REPORT_URL,
                    "atpDoubles": ATP_OFFICIAL_DOUBLES_RANKINGS_REPORT_URL,
                    "atpProfiles": ATP_PLAYER_PROFILE_URL_TEMPLATE,
                    "wtaSingles": WTA_OFFICIAL_RANKINGS_URL,
                    "wtaDoubles": WTA_OFFICIAL_DOUBLES_URL,
                },
                "players": PLAYERS_URL,
                "training": [TRAINING_URL_TEMPLATE.format(day=0), TRAINING_URL_TEMPLATE.format(day=1)],
            },
            "trainingDays": training_days,
            "audit": {
                "doublesMatches": len(doubles_matches),
                "atpDrawFallbackMatches": atp_draw_fallback_count,
                "wtaDrawFallbackMatches": wta_draw_fallback_count,
                "doublesPlayers": len(doubles_player_ids),
                "doublesPlayersMissingDoublesRanking": sum(
                    1
                    for player_id in doubles_player_ids
                    if registry.get(player_id, {}).get("doublesRanking") in (None, "")
                    and registry.get(player_id, {}).get("ranking") in (None, "")
                ),
                "playersMissingTour": sum(1 for player in players if not str(player.get("tour") or "").strip()),
                "atpDrawEvents": [
                    str(event.get("EventTypeCode") or "")
                    for association in (atp_draw_payload.get("Associations") or [])
                    for event in association.get("Events") or []
                ],
            },
        },
        "players": players,
        "matches": matches,
        "trainingSessions": training_sessions,
    }


def main() -> int:
    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1]).expanduser().resolve()
    else:
        output_path = Path(__file__).resolve().parents[1] / "data" / "latest.json"

    output = build_output()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Saved snapshot to {output_path}")
    print(f"Players: {len(output['players'])}, matches: {len(output['matches'])}, training sessions: {len(output['trainingSessions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
