"""
PHASE36 v1.12 — CUDA ENVIRONMENT READINESS DIAGNOSIS ONLY.

GOVERNANCE (strict):
  * NO torch.load, NO checkpoint read/deserialization.
  * NO model construction, NO forward, NO training.
  * NO VAL image/GT read, NO TEST read, NO ROUTER_HOLDOUT read.
  * NO smoke, NO science.
  * The ONLY repo function invoked is src.utils.device.get_device(require_cuda=True)
    as a device-resolution diagnostic (the exact call that failed in the smoke).
  * Nothing is constructed afterward.
"""
import json, os, platform, subprocess, sys, datetime

OUT = r"D:\Softfors\jup\reports\audits\phase36_v1_12_cuda_environment_diagnosis.json"

def sha256_of(p):
    import hashlib
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    except Exception:
        return None

diag = {
    "artifact": "phase36_v1_12_cuda_environment_diagnosis",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_12",
    "type": "CUDA_ENVIRONMENT_READINESS_DIAGNOSIS",
    "governance": {
        "diagnostic_only": True,
        "torch_load": False,
        "checkpoint_read": False,
        "model_construction": False,
        "forward_pass": False,
        "val_image_read": False,
        "gt_read": False,
        "test_read": False,
        "router_holdout_read": False,
        "smoke": False,
        "science": False,
        "training": False,
        "note": "Only device/environment queries. src.utils.device.get_device(require_cuda=True) is called purely as a device-resolution diagnostic.",
    },
    "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
}

# 1. python executable path
diag["python_executable"] = sys.executable
# 2. python version
diag["python_version"] = sys.version.replace("\n", " ")
diag["python_version_info"] = list(sys.version_info[:3])
# 3. operating system
diag["operating_system"] = {
    "platform": platform.platform(),
    "system": platform.system(),
    "release": platform.release(),
    "version": platform.version(),
    "machine": platform.machine(),
}
diag["virtual_env"] = {
    "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
    "CONDA_PREFIX": os.environ.get("CONDA_PREFIX"),
    "sys_prefix": sys.prefix,
    "sys_base_prefix": sys.base_prefix,
    "in_venv": sys.prefix != sys.base_prefix,
    "repo_venv_expected": r"D:\Softfors\jup\.venv\Scripts\python.exe",
}

# 4/5. NVIDIA driver availability + nvidia-smi summary
def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "executable not found"
    except Exception as e:
        return 1, "", repr(e)

rc, out, err = run(["nvidia-smi", "-L"])
diag["nvidia_smi_list_rc"] = rc
diag["nvidia_smi_list_stdout"] = out
diag["nvidia_smi_list_stderr"] = err
diag["nvidia_driver_available"] = (rc == 0 and out != "")

rc2, out2, err2 = run(["nvidia-smi"])
diag["nvidia_smi_summary_rc"] = rc2
diag["nvidia_smi_summary_stdout"] = out2
diag["nvidia_smi_summary_stderr"] = err2

# 6-13. torch device info
try:
    import torch
    diag["torch_imported"] = True
    diag["torch_version"] = torch.__version__
    diag["torch_version_cuda"] = torch.version.cuda          # 7
    diag["torch_cuda_is_available"] = bool(torch.cuda.is_available())  # 8
    diag["torch_cuda_device_count"] = int(torch.cuda.device_count())   # 9
    diag["torch_cuda_current_device"] = (int(torch.cuda.current_device())
                                         if torch.cuda.is_available() else None)  # 10
    diag["torch_cuda_device_name_0"] = (torch.cuda.get_device_name(0)
                                        if torch.cuda.is_available() else None)   # 11
    try:
        diag["torch_backends_cudnn_version"] = torch.backends.cudnn.version()     # 12
    except Exception as e:
        diag["torch_backends_cudnn_version"] = None
        diag["torch_backends_cudnn_version_error"] = repr(e)
    diag["torch_cuda_capability_0"] = (list(torch.cuda.get_device_capability(0))
                                       if torch.cuda.is_available() else None)
    # Extra: is this a CPU-only build?
    diag["torch_is_cpu_only_build"] = (torch.version.cuda is None)
    diag["torch_cuda_compiled"] = torch.version.cuda is not None
except Exception as e:
    diag["torch_imported"] = False
    diag["torch_import_error"] = repr(e)

# 13. CUDA_VISIBLE_DEVICES
cvd = os.environ.get("CUDA_VISIBLE_DEVICES")
diag["CUDA_VISIBLE_DEVICES"] = cvd
diag["CUDA_VISIBLE_DEVICES_effect"] = (
    "HIDES_ALL_GPUS" if cvd is not None and cvd.strip() in ("", "-1") else
    ("SET" if cvd is not None else "UNSET")
)
# extra env
for k in ("CUDA_HOME", "CUDA_PATH", "CUDA_ROOT", "TORCH_CUDA_ARCH_LIST", "NVIDIA_VISIBLE_DEVICES"):
    diag[f"env_{k}"] = os.environ.get(k)

# 14. get_device(require_cuda=True) diagnostic
try:
    sys.path.insert(0, r"D:\Softfors\jup")
    from src.utils.device import get_device, CudaUnavailableError, device_report
    try:
        dev = get_device(require_cuda=True)
        diag["get_device_require_cuda_success"] = True
        diag["get_device_resolved"] = str(dev)
        diag["get_device_error"] = None
    except Exception as e:
        diag["get_device_require_cuda_success"] = False
        diag["get_device_resolved"] = None
        diag["get_device_error"] = {"type": type(e).__name__, "message": str(e)}
    try:
        diag["src_device_report"] = device_report()
    except Exception as e:
        diag["src_device_report_error"] = repr(e)
except Exception as e:
    diag["get_device_import_error"] = repr(e)
    diag["get_device_require_cuda_success"] = None

# failure grounding
diag["failed_smoke_grounding"] = {
    "smoke_failure_artifact": "reports/audits/phase36_robustness_smoke_failure_v1_12.json",
    "smoke_failure_sha256": sha256_of(r"D:\Softfors\jup\reports\audits\phase36_robustness_smoke_failure_v1_12.json"),
    "exception_type": "CudaUnavailableError",
    "failing_stage": "run_smoke_exception (pre-model CUDA device resolution)",
}

# root-cause classification
causes = []
if diag.get("torch_imported") and diag.get("torch_is_cpu_only_build"):
    causes.append("B_CPU_ONLY_PYTORCH_BUILD")
if diag.get("torch_imported") and not diag.get("torch_is_cpu_only_build") and not diag.get("torch_cuda_is_available"):
    causes.append("C_CUDA_ENABLED_TORCH_BUT_DRIVER_OR_RUNTIME_INCOMPATIBILITY")
if not diag.get("nvidia_driver_available") and not diag.get("torch_is_cpu_only_build"):
    causes.insert(0, "A_NVIDIA_GPU_OR_DRIVER_UNAVAILABLE")
if diag.get("CUDA_VISIBLE_DEVICES_effect") == "HIDES_ALL_GPUS":
    causes.append("D_GPU_HIDDEN_BY_CUDA_VISIBLE_DEVICES")
if not diag.get("virtual_env", {}).get("in_venv"):
    causes.append("E_WRONG_PYTHON_OR_VENV_INTERPRETER")
diag["root_cause_candidates"] = causes
diag["root_cause_primary"] = causes[0] if causes else "F_OTHER_ENVIRONMENT_PROBLEM"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(diag, f, indent=1)
print(json.dumps({k: diag[k] for k in (
    "python_executable","python_version","torch_version","torch_version_cuda",
    "torch_cuda_is_available","torch_cuda_device_count","torch_is_cpu_only_build",
    "nvidia_driver_available","nvidia_smi_list_stdout","CUDA_VISIBLE_DEVICES",
    "CUDA_VISIBLE_DEVICES_effect","get_device_require_cuda_success","get_device_error",
    "root_cause_candidates","root_cause_primary")}, indent=1))
