from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("CFAA_DATA_DIR", str(ROOT / "data"))).resolve()
DATA.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.environ.get(
    "CFAA_DATABASE_URL", "sqlite:///" + (DATA / "cfaa.db").as_posix()
)
MAX_UPLOAD = 20 * 1024 * 1024

# Keep multipart spool files inside the protected runtime data directory.
import tempfile

TEMP = DATA / "tmp"
TEMP.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEMP)

import json

CATEGORIES = json.loads(
    os.environ.get(
        "CFAA_CATEGORIES",
        json.dumps(
            [
                "Online financial fraud",
                "Identity theft",
                "Unauthorized access",
                "Cyber harassment",
                "Online sexual exploitation investigations",
                "Cryptocurrency-related fraud",
                "Data breaches",
                "Other cybercrime investigations",
            ]
        ),
    )
)
if (
    not isinstance(CATEGORIES, list)
    or not CATEGORIES
    or len(CATEGORIES) > 100
    or not all(isinstance(c, str) and 0 < len(c) <= 100 for c in CATEGORIES)
):
    raise ValueError("CFAA_CATEGORIES must be a JSON list of 1 to 100 category names")
