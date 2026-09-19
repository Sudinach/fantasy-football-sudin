"""CI entrypoint: runs one analysis pass and writes the resulting Snapshot.

Usage: uv run python scripts/run_snapshot.py <entry_id>

Writes data/snapshots/latest.json (overwritten every run, the canonical file
the Next.js frontend reads) and an append-only copy under
data/snapshots/archive/, which doubles as free historical data (see
CONTEXT.md's "Snapshot" definition).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fpl_analysis.pipeline import run
from fpl_analysis.snapshot import build_snapshot

SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "snapshots"


def main(entry_id: int) -> None:
    result = run(entry_id)
    snapshot = build_snapshot(result)

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    (SNAPSHOTS_DIR / "latest.json").write_text(json.dumps(snapshot, indent=2) + "\n")

    archive_dir = SNAPSHOTS_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"{snapshot['generated_at'].replace(':', '')}_gw{result.gameweek}.json"
    (archive_dir / archive_name).write_text(json.dumps(snapshot, indent=2) + "\n")

    print(f"wrote {SNAPSHOTS_DIR / 'latest.json'}")
    print(f"wrote {archive_dir / archive_name}")
    print(f"{len(snapshot['squad'])} squad players, {len(snapshot['suggestions'])} suggestions")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: run_snapshot.py <entry_id>")
        raise SystemExit(1)
    main(int(sys.argv[1]))
