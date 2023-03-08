import sys
from pathlib import Path


# handle the wonky path handling currently relied upon by analysis code
sys.path.append(str(Path(__file__).parents[1] / "analysis"))
