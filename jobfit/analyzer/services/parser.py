"""File handling + regex extraction."""
import re
from pathlib import Path

SECTION_SPLIT = re.compile(r"^\s*(nice to have|preferred|good to have|bonus)\b.*$",
                           re.IGNORECASE | re.MULTILINE)
EXPERIENCE_RE = re.compile(r"(\d+)\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def read_text_file(path):
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def load_skill_catalog(path):
    """Read data/skills.txt -> {alias: canonical_skill}."""
    catalog = {}
    for line in read_text_file(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        canonical, _, aliases = line.partition(":")
        canonical = canonical.strip().lower()
        catalog[canonical] = canonical
        for alias in aliases.split(","):
            if alias.strip():
                catalog[alias.strip().lower()] = canonical
    return catalog


def extract_skills(text, catalog):
    """Return a SET of canonical skills found in text (regex, whole-word safe for c++/c#)."""
    found = set()
    for alias, canonical in catalog.items():
        pattern = r"(?<![A-Za-z0-9+#])" + re.escape(alias) + r"(?![A-Za-z0-9+#])"
        if re.search(pattern, text, re.IGNORECASE):
            found.add(canonical)
    return found


def split_job_sections(job_text):
    """Split job text into (required_text, preferred_text)."""
    match = SECTION_SPLIT.search(job_text)
    if not match:
        return job_text, ""
    return job_text[:match.start()], job_text[match.start():]


def extract_years(text):
    """Highest 'N years' mention in text, else 0."""
    nums = [int(n) for n in EXPERIENCE_RE.findall(text)]
    return max(nums) if nums else 0


def extract_email(text):
    m = EMAIL_RE.search(text)
    return m.group(0) if m else ""
