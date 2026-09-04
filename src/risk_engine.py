import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# PATHS / SETTINGS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_RISK_FILE = (
    PROJECT_ROOT
    / "data"
    / "players"
    / "player_risks.json"
)

SLEEPER_CACHE_FILE = (
    PROJECT_ROOT
    / "data"
    / "players"
    / "sleeper_players_cache.json"
)

SLEEPER_PLAYERS_URL = (
    "https://api.sleeper.app/v1/players/nfl"
)

# Sleeper recommends refreshing the full player map
# no more than about once per day.
CACHE_MAX_AGE_SECONDS = 24 * 60 * 60

HTTP_TIMEOUT_SECONDS = 20


# ============================================================
# NAME NORMALIZATION
# ============================================================

def _normalize_name(name):
    """
    Normalize player names so rankings and Sleeper names
    have a better chance of matching.

    Examples:
    - Curly apostrophes become normal text
    - Accents are removed
    - Punctuation is ignored
    - Jr./Sr./II/III/IV suffixes are removed
    """

    if name is None:
        return ""

    text = str(name).strip().lower()

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(
            character
        )
    )

    text = text.replace(
        "’",
        "'"
    )

    text = re.sub(
        r"[.'’-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    suffixes = {
        "jr",
        "sr",
        "ii",
        "iii",
        "iv",
        "v",
    }

    parts = text.split()

    while (
        parts
        and parts[-1] in suffixes
    ):
        parts.pop()

    return " ".join(parts)


# ============================================================
# MANUAL RISK FILE
# ============================================================

def _load_manual_risks(
    path=None
):
    """
    Load manually maintained risk notes.

    Manual entries are used for things that an automated
    feed may miss or describe poorly, such as:
    - suspension / legal
    - contract dispute
    - unusual roster status
    - depth-chart / role concern
    - any special draft-night note Scott wants to preserve

    Missing or malformed files never crash the War Room.
    """

    risk_path = (
        Path(path)
        if path
        else DEFAULT_RISK_FILE
    )

    if not risk_path.exists():
        return {}

    try:
        with risk_path.open(
            "r",
            encoding="utf-8"
        ) as file_handle:

            raw_data = json.load(
                file_handle
            )

    except (
        OSError,
        json.JSONDecodeError
    ):
        return {}

    if isinstance(
        raw_data,
        dict
    ):
        entries = raw_data.get(
            "players",
            []
        )

    elif isinstance(
        raw_data,
        list
    ):
        entries = raw_data

    else:
        entries = []

    risks = {}

    for entry in entries:

        if not isinstance(
            entry,
            dict
        ):
            continue

        player_name = entry.get(
            "player"
        )

        if not player_name:
            continue

        normalized = _normalize_name(
            player_name
        )

        if not normalized:
            continue

        # Active=False means "ignore this manual record".
        if entry.get(
            "active",
            True
        ) is False:
            continue

        cleaned = dict(
            entry
        )

        cleaned.setdefault(
            "level",
            "INFO"
        )

        cleaned.setdefault(
            "category",
            "STATUS"
        )

        cleaned.setdefault(
            "source",
            "Manual"
        )

        risks[
            normalized
        ] = cleaned

    return risks


# ============================================================
# SLEEPER CACHE
# ============================================================

def _cache_is_fresh(
    cache_path
):
    """
    True when the local Sleeper cache is younger
    than 24 hours.
    """

    if not cache_path.exists():
        return False

    try:
        age_seconds = (
            time.time()
            - cache_path.stat().st_mtime
        )

    except OSError:
        return False

    return (
        age_seconds
        < CACHE_MAX_AGE_SECONDS
    )


def _read_json_file(
    path
):
    """
    Read a JSON file safely.
    """

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as file_handle:

            return json.load(
                file_handle
            )

    except (
        OSError,
        json.JSONDecodeError
    ):
        return None


def _write_json_file(
    path,
    data
):
    """
    Write cache data safely.

    A failure to write the cache must never stop
    Fantasy War Room from running.
    """

    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with path.open(
            "w",
            encoding="utf-8"
        ) as file_handle:

            json.dump(
                data,
                file_handle
            )

    except OSError:
        pass


# ============================================================
# SLEEPER DOWNLOAD
# ============================================================

def _download_sleeper_players():
    """
    Download Sleeper's NFL player map.

    Returns:
        dict on success
        None on failure
    """

    request = urllib.request.Request(
        SLEEPER_PLAYERS_URL,
        headers={
            "User-Agent":
                "Fantasy-War-Room/1.0"
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=HTTP_TIMEOUT_SECONDS
        ) as response:

            payload = response.read()

        data = json.loads(
            payload.decode(
                "utf-8"
            )
        )

        if isinstance(
            data,
            dict
        ):
            return data

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError
    ):
        return None

    return None


def _load_sleeper_players():
    """
    Load the Sleeper player map with a 24-hour cache.

    Order of preference:
    1. Fresh local cache
    2. New Sleeper download
    3. Stale cache as fallback if Sleeper is unavailable
    4. Empty dictionary

    That means a temporary internet/API problem will
    not break the draft application.
    """

    if _cache_is_fresh(
        SLEEPER_CACHE_FILE
    ):

        cached = _read_json_file(
            SLEEPER_CACHE_FILE
        )

        if isinstance(
            cached,
            dict
        ):
            return cached

    downloaded = (
        _download_sleeper_players()
    )

    if isinstance(
        downloaded,
        dict
    ):

        _write_json_file(
            SLEEPER_CACHE_FILE,
            downloaded
        )

        return downloaded

    stale_cache = _read_json_file(
        SLEEPER_CACHE_FILE
    )

    if isinstance(
        stale_cache,
        dict
    ):
        return stale_cache

    return {}


# ============================================================
# SLEEPER PLAYER NAME
# ============================================================

def _get_sleeper_full_name(
    player
):
    """
    Build a Sleeper player's display name.
    """

    full_name = player.get(
        "full_name"
    )

    if full_name:
        return str(
            full_name
        ).strip()

    first_name = str(
        player.get(
            "first_name",
            ""
        )
    ).strip()

    last_name = str(
        player.get(
            "last_name",
            ""
        )
    ).strip()

    return (
        f"{first_name} {last_name}"
        .strip()
    )


# ============================================================
# AUTOMATIC RISK CLASSIFICATION
# ============================================================

def _classify_sleeper_risk(
    player
):
    """
    Convert Sleeper player fields into a War Room risk record.

    We intentionally keep this conservative.
    No warning is created unless Sleeper provides a
    meaningful status/injury/practice signal.

    Risk is INFORMATIONAL ONLY.
    It does not change Recommendation Score.
    """

    player_name = (
        _get_sleeper_full_name(
            player
        )
    )

    if not player_name:
        return None

    status = str(
        player.get(
            "status",
            ""
        )
        or ""
    ).strip()

    injury_status = str(
        player.get(
            "injury_status",
            ""
        )
        or ""
    ).strip()

    practice = str(
        player.get(
            "practice_participation",
            ""
        )
        or ""
    ).strip()

    injury_start = str(
        player.get(
            "injury_start_date",
            ""
        )
        or ""
    ).strip()

    depth_order = player.get(
        "depth_chart_order"
    )

    status_lower = (
        status.lower()
    )

    injury_lower = (
        injury_status.lower()
    )

    practice_lower = (
        practice.lower()
    )

    level = None
    category = None
    reasons = []

    # --------------------------------------------------------
    # HIGH RISK — player availability / roster status
    # --------------------------------------------------------

    high_status_terms = [
        "injured reserve",
        "ir",
        "physically unable",
        "pup",
        "non-football injury",
        "nfi",
        "suspended",
        "suspension",
        "inactive",
    ]

    if any(
        term == status_lower
        or term in status_lower
        for term in high_status_terms
    ):

        level = "HIGH"
        category = "STATUS"

        if status:
            reasons.append(
                f"Status: {status}"
            )

    # --------------------------------------------------------
    # HIGH RISK — injury status
    # --------------------------------------------------------

    high_injury_terms = [
        "out",
        "ir",
        "pup",
    ]

    if any(
        term == injury_lower
        for term in high_injury_terms
    ):

        level = "HIGH"
        category = "INJURY"

        if injury_status:
            reasons.append(
                f"Injury status: "
                f"{injury_status}"
            )

    # --------------------------------------------------------
    # MEDIUM RISK — injury designation
    # --------------------------------------------------------

    medium_injury_terms = [
        "doubtful",
        "questionable",
    ]

    if (
        level != "HIGH"
        and any(
            term == injury_lower
            for term in medium_injury_terms
        )
    ):

        level = "MEDIUM"
        category = "INJURY"

        reasons.append(
            f"Injury status: "
            f"{injury_status}"
        )

    # --------------------------------------------------------
    # MEDIUM RISK — practice participation
    # --------------------------------------------------------

    practice_risk_terms = [
        "did not participate",
        "dnp",
        "limited",
    ]

    practice_has_risk = any(
        term in practice_lower
        for term in practice_risk_terms
    )

    if practice_has_risk:

        if level is None:
            level = "MEDIUM"
            category = "INJURY"

        if practice:
            reasons.append(
                f"Practice: {practice}"
            )

    # --------------------------------------------------------
    # NO SIGNAL = NO WARNING
    # --------------------------------------------------------

    if level is None:
        return None

    # --------------------------------------------------------
    # Helpful supporting context
    # --------------------------------------------------------

    if (
        injury_start
        and injury_start.lower()
        not in {
            "none",
            "null",
            "nan",
        }
    ):

        reasons.append(
            f"Injury start: "
            f"{injury_start}"
        )

    if (
        depth_order is not None
        and str(
            depth_order
        ).strip()
    ):

        reasons.append(
            f"Depth chart order: "
            f"{depth_order}"
        )

    # De-duplicate while preserving order.
    reasons = list(
        dict.fromkeys(
            reasons
        )
    )

    summary = "; ".join(
        reasons
    )

    if not summary:
        summary = (
            "Sleeper reports a player "
            "availability concern."
        )

    updated = (
        datetime.now(
            timezone.utc
        )
        .date()
        .isoformat()
    )

    return {
        "player":
            player_name,

        "active":
            True,

        "level":
            level,

        "category":
            category,

        "summary":
            summary,

        "source":
            "Sleeper",

        "updated":
            updated,

        "sleeper_player_id":
            player.get(
                "player_id"
            ),
    }


# ============================================================
# BUILD AUTOMATIC SLEEPER RISK MAP
# ============================================================

def _build_sleeper_risks():
    """
    Convert Sleeper's complete player map into only
    the players who currently carry a meaningful
    automated risk signal.
    """

    sleeper_players = (
        _load_sleeper_players()
    )

    risks = {}

    for sleeper_player in (
        sleeper_players.values()
    ):

        if not isinstance(
            sleeper_player,
            dict
        ):
            continue

        risk = _classify_sleeper_risk(
            sleeper_player
        )

        if not risk:
            continue

        normalized = _normalize_name(
            risk["player"]
        )

        if normalized:
            risks[
                normalized
            ] = risk

    return risks


# ============================================================
# PUBLIC RISK LOADER
# ============================================================

def load_player_risks(
    path=None
):
    """
    Load one unified War Room risk dictionary.

    Automatic Sleeper risks are loaded first.
    Active manual entries then overwrite Sleeper
    entries for the same player.

    This gives Scott an intentional manual override
    whenever a special situation needs better context.
    """

    sleeper_risks = (
        _build_sleeper_risks()
    )

    manual_risks = (
        _load_manual_risks(
            path
        )
    )

    combined = dict(
        sleeper_risks
    )

    combined.update(
        manual_risks
    )

    return combined


# ============================================================
# PUBLIC PLAYER LOOKUP
# ============================================================

def get_player_risk(
    player_name,
    risks
):
    """
    Return the unified risk record for one player.

    Returns None when no active risk exists.
    """

    if not risks:
        return None

    normalized = _normalize_name(
        player_name
    )

    if not normalized:
        return None

    risk = risks.get(
        normalized
    )

    if not risk:
        return None

    if risk.get(
        "active",
        True
    ) is False:
        return None

    return risk


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    risks = load_player_risks()

    print(
        "Risk Engine loaded successfully."
    )

    print(
        f"Active risk records: "
        f"{len(risks)}"
    )

    manual_count = len(
        _load_manual_risks()
    )

    print(
        f"Manual risk records: "
        f"{manual_count}"
    )

    print(
        f"Automatic Sleeper risk records: "
        f"{max(0, len(risks) - manual_count)}"
    )
