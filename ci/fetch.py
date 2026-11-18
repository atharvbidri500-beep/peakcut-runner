# The runner's first step: pull PeakCut's code and the studio's saved state from the private
# dataset repo, so every round starts exactly where the last one left off.
#
# One brain only: the engine that is really running writes data/heartbeat.json every five minutes.
# A fresh heartbeat means the PC is alive and THIS round must not post (two engines would post the
# same clip twice). When the heartbeat is silent for half an hour the PC is gone and the cloud works.
import datetime
import json
import os
import tarfile
import time
from pathlib import Path

from huggingface_hub import hf_hub_download

HEARTBEAT = 30 * 60          # seconds of silence before the cloud takes over

for name in ("code.tar.gz", "state.tar.gz"):
    p = Path(hf_hub_download(repo_id=os.environ["PEAKCUT_SNAPSHOT"], filename=name,
                             repo_type="dataset", token=os.environ["HF_TOKEN"]))
    with tarfile.open(p, "r:gz") as t:
        try:
            t.extractall(".", filter="data")
        except TypeError:
            t.extractall(".")

try:                                   # the compact copies of clips still waiting to post
    p = Path(hf_hub_download(repo_id=os.environ["PEAKCUT_SNAPSHOT"], filename="queue.tar.gz",
                             repo_type="dataset", token=os.environ["HF_TOKEN"]))
    with tarfile.open(p, "r:gz") as t:
        try:
            t.extractall(".", filter="data")
        except TypeError:
            t.extractall(".")
    print("posting queue restored")
except Exception:
    print("no posting queue saved yet")

age = None
try:
    beat = json.loads(Path("data/heartbeat.json").read_text())
    if beat.get("role") == "pc":
        age = time.time() - float(beat.get("at") or 0)
        print(f"the PC heartbeat is {age / 60:.0f} minutes old")
except Exception:
    pass

if age is None:                        # no heartbeat file: fall back to how fresh the archive is
    from huggingface_hub import HfApi
    commits = list(HfApi(token=os.environ["HF_TOKEN"]).list_repo_commits(
        os.environ["PEAKCUT_SNAPSHOT"], repo_type="dataset"))
    if commits:
        stamp = commits[0].created_at
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=datetime.timezone.utc)
        age = (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds()
        print(f"no heartbeat file; last repo save was {age / 60:.0f} minutes ago")

if age is not None and age < HEARTBEAT:
    with open(os.environ["GITHUB_ENV"], "a") as f:
        f.write("SKIP_ROUND=1\n")
    print("The PC is alive - this round steps aside.")
else:
    print("No PC heartbeat - the cloud takes over.")
