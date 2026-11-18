# The runner's first step: pull PeakCut's code and the studio's saved state from the private
# dataset repo, so every round starts exactly where the last one left off.
import os
import tarfile
from pathlib import Path

from huggingface_hub import hf_hub_download

token = os.environ["HF_TOKEN"]
for name in ("code.tar.gz", "state.tar.gz"):
    p = Path(hf_hub_download(repo_id=os.environ["PEAKCUT_SNAPSHOT"], filename=name,
                             repo_type="dataset", token=token))
    with tarfile.open(p, "r:gz") as t:
        try:
            t.extractall(".", filter="data")
        except TypeError:
            t.extractall(".")
    print(name, "restored")
