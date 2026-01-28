"""
Compatibility shim for vis_utils.
Redirects to src.visualization.utils.
"""
import sys
from pathlib import Path

# Ensure src is in path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.visualization.utils import *
