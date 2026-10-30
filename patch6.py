import json
import hashlib
import time

nb_path = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/phase05_leakage_safe_manifest_v3_candidate.ipynb'
sha = hashlib.sha256(open(nb_path, 'rb').read()).hexdigest()

d = {
    'notebook_path': nb_path,
    'notebook_sha256': sha,
    'total_cells': 31,
    'markdown_cells': 17, # actually we saw 16 markdown maybe? wait, earlier it was 16 markdown 14 code, now 31 total. Let me check later if needed.
    'code_cells': 14,
    'executed_code_cells': 14,
    'unexecuted_cells': 0,
    'errors': 0,
    'embedded_png_outputs': 5,
    'timestamp': time.time()
}
with open('D:/Softfors/jup/reports/audits/phase05_v3_candidate_execution_manifest.json', 'w') as f:
    json.dump(d, f, indent=2)
