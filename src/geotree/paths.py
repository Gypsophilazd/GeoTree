"""Host-side paths; credentials are never transferred to the task."""
import os
from pathlib import Path

def runtime_dir():
    return Path(os.environ.get("GEOTREE_RUN_ROOT", str(Path.cwd()/".geotree"))).resolve()
