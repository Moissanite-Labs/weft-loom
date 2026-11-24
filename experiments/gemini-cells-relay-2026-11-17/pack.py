#!/usr/bin/env python3
"""Copy finished runs from the run root into results/, packed for the repository.

    python3 pack.py /srv/gc-live

For each run it copies `log.jsonl` as it is and packs the build traces and every harness
snapshot into `artifacts.tar.gz`. Before anything is written it scans the text for e-mail
addresses and session links and refuses to pack a run that holds one: the model transport
adds account notes to every call, and none of that may reach a public repository.
"""

import hashlib
import io
import re
import shutil
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIVATE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|claude\.ai/code/session_|session_01[A-Za-z0-9]{10,}")
ALLOWED = {"noreply@anthropic.com"}


def private_hits(text: str) -> list[str]:
    return sorted({m for m in PRIVATE.findall(text) if m not in ALLOWED})


def main() -> int:
    root = Path(sys.argv[1])
    out = HERE / "results" / "runs"
    out.mkdir(parents=True, exist_ok=True)
    manifest, refused = [], []
    for run in sorted((root / "runs").iterdir()):
        log = run / "log.jsonl"
        if not log.exists():
            continue
        files = [log] + sorted((run / "builds").glob("*.txt")) + sorted(p for p in (run / "snap").rglob("*") if p.is_file())
        hits = []
        for f in files:
            hits += private_hits(f.read_text(errors="replace"))
        if hits:
            refused.append((run.name, sorted(set(hits))[:5]))
            continue
        dst = out / run.name
        dst.mkdir(exist_ok=True)
        shutil.copy(log, dst / "log.jsonl")
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=9) as tar:
            for f in files[1:]:
                info = tar.gettarinfo(str(f), arcname=str(f.relative_to(run)))
                info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
                with open(f, "rb") as fh:
                    tar.addfile(info, fh)
        (dst / "artifacts.tar.gz").write_bytes(buf.getvalue())
        for name in ("log.jsonl", "artifacts.tar.gz"):
            manifest.append(f"{hashlib.sha256((dst / name).read_bytes()).hexdigest()}  runs/{run.name}/{name}")
    # runs set aside for a referee fault: the log is kept as the record of the fault
    fdst = HERE / "results" / "faulted"
    for run in sorted((root / "faulted").iterdir()) if (root / "faulted").is_dir() else []:
        for name in ("log.jsonl", "exam_resit.jsonl"):
            f = run / name
            if not f.exists():
                continue
            if private_hits(f.read_text(errors="replace")):
                refused.append((f"faulted/{run.name}/{name}", ["private text"]))
                continue
            (fdst / run.name).mkdir(parents=True, exist_ok=True)
            shutil.copy(f, fdst / run.name / name)
            manifest.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  faulted/{run.name}/{name}")
    for f in sorted(root.glob("kexam-*.jsonl")):
        if private_hits(f.read_text(errors="replace")):
            refused.append((f.name, ["private text"]))
            continue
        shutil.copy(f, HERE / "results" / f.name)
        manifest.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
    for f in sorted(root.glob("assay*.jsonl")):
        hits = private_hits(f.read_text(errors="replace"))
        if hits:
            refused.append((f.name, hits[:5]))
            continue
        shutil.copy(f, HERE / "results" / f.name)
        manifest.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
    (HERE / "results" / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n")
    print(f"packed {len([m for m in manifest if m.endswith('log.jsonl')])} runs, refused {len(refused)}")
    for name, hits in refused:
        print("REFUSED", name, hits)
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
