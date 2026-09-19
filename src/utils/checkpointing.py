"""Restart-safe full-state checkpoints."""
from pathlib import Path
import torch
from .reproducibility import capture_random_state, restore_random_state


def save_training_checkpoint(path, model, optimizer, scheduler, scaler, epoch, global_step,
                             best_validation_score, configuration, seed, training_history,
                             manifest_version, manifest_hashes, experiment_id, model_name,
                             input_resolution, threshold, git_commit=None,
                             early_stopping_state=None, loader_generator_states=None):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    state={"model_state":model.state_dict(),"optimizer_state":optimizer.state_dict(),
           "scheduler_state":scheduler.state_dict() if scheduler else None,
           "grad_scaler_state":scaler.state_dict() if scaler else None,"epoch":epoch,
           "global_step":global_step,"best_validation_score":best_validation_score,
           "configuration":configuration,"seed":seed,"training_history":training_history,
           "manifest_version":manifest_version,"manifest_hashes":manifest_hashes,
           "experiment_id":experiment_id,"model_name":model_name,"input_resolution":input_resolution,
           "threshold":threshold,"git_commit":git_commit,"pytorch_version":torch.__version__,
           "cuda_available":torch.cuda.is_available(),"cuda_runtime":torch.version.cuda,
           "gpu_name":torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "random_state":capture_random_state(),
           "early_stopping_state":early_stopping_state,
           "loader_generator_states":loader_generator_states}
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(state, temporary)
    # Validate the completed temporary archive before replacing the prior checkpoint.
    torch.load(temporary, map_location="cpu", weights_only=False)
    import time
    for _attempt in range(10):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            time.sleep(0.5)
    return path


def load_training_checkpoint(path, model, optimizer=None, scheduler=None, scaler=None,
                             restore_rng=True, map_location="cpu"):
    state=torch.load(path,map_location=map_location,weights_only=False); model.load_state_dict(state["model_state"])
    if optimizer is not None: optimizer.load_state_dict(state["optimizer_state"])
    if scheduler is not None and state["scheduler_state"] is not None: scheduler.load_state_dict(state["scheduler_state"])
    if scaler is not None and state["grad_scaler_state"] is not None: scaler.load_state_dict(state["grad_scaler_state"])
    if restore_rng: restore_random_state(state["random_state"])
    return state
