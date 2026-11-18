# The runner's first step: pull PeakCut's code and the studio's saved state from the private
# dataset repo, so every round starts exactly where the last one left off.
#
# One brain only: the saved state doubles as a heartbeat. The studio that runs on the real PC
# backs itself up every five minutes, so a fresh archive means that engine is alive and THIS
# round must not post anything (two engines would post the same clip twice). When the archive
# has been quiet for half an hour the PC is gone, and the cloud becomes the engine.
import datetime
import os
import tarfile
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
    print(name, "restored")

from huggingface_hub import HfApi  # noqa: E402
commits = list(HfApi(token=os.environ["HF_TOKEN"]).list_repo_commits(
    os.environ["PEAKCUT_SNAPSHOT"], repo_type="dataset"))
age = 1e18
if commits:
    stamp = commits[0].created_at
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=datetime.timezone.utc)
    age = (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds()
print(f"last save was {age / 60:.0f} minutes ago")

if age < HEARTBEAT:
    with open(os.environ["GITHUB_ENV"], "a") as f:
        f.write("SKIP_ROUND=1\n")
    print("Another engine (the PC) is alive and keeping the state fresh - this round steps aside.")
else:
    print("No other engine has spoken in half an hour - the cloud takes over.")
