from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
src_path = root / "src"
sys.path.insert(0, str(src_path))
