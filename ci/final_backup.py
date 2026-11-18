# The runner's last step: save the round's state back to the dataset repo (the server is
# already stopped, so nothing can change under us).
import os
import sys
import tarfile
from pathlib import Path

import tarfile
from huggingface_hub import HfApi

sys.path.insert(0, str(Path.cwd()))     # the code bundle is extracted beside the ci folder
from studio import config, snapshot

out = Path("final_state.tar.gz")
n = snapshot._write(out)
HfApi(token=os.environ["HF_TOKEN"]).upload_file(
    path_or_fileobj=str(out), path_in_repo="state.tar.gz",
    repo_id=os.environ["PEAKCUT_SNAPSHOT"], repo_type="dataset")
print(f"final backup: {n} files")
