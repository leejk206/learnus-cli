import re
from datetime import datetime

_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})")
_LATE_RE = re.compile(r"지각\s*:\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})")


def parse_ubstrap(text: str) -> tuple[datetime | None, datetime | None, datetime | None]:
    """Parse span.text-ubstrap content.

    Examples:
      "2026-04-14 00:00:00 ~ 2026-04-20 23:59:59 (지각 : 2026-04-27 23:59:59)"
      "2026-04-14 00:00:00 ~ 2026-04-20 23:59:59"
    """
    if not text:
        return None, None, None
    dates = _DATE_RE.findall(text)
    if len(dates) < 2:
        return None, None, None
    start = _tuple_to_dt(dates[0])
    end = _tuple_to_dt(dates[1])
    late = None
    late_m = _LATE_RE.search(text)
    if late_m:
        late = _tuple_to_dt(late_m.groups())
    return start, end, late


def _tuple_to_dt(t) -> datetime:
    y, mo, d, h, mi, s = (int(x) for x in t)
    return datetime(y, mo, d, h, mi, s)
