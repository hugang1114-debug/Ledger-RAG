import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_snapshot.index_promotion import promote_snapshot_index_metadata


def main():
    parser = argparse.ArgumentParser(description="Promote Gate 8J snapshot/index metadata.")
    parser.add_argument("--registry", required=True, help="Path to snapshots/main_v1/source_snapshots.json.")
    parser.add_argument("--readiness-config", required=True, help="Path to configs/gate8/main_v1_readiness.yaml.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root for resolving local artifact paths.")
    args = parser.parse_args()

    summary = promote_snapshot_index_metadata(args.registry, args.readiness_config, Path(args.repo_root))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["promoted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
