import traceback
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"D:\Softfors\jup")))

try:
    from post_phase13_h2a_downstream_eval import main
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
