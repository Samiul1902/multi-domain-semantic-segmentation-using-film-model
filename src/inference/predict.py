"""Generic multi-domain prediction interface for RA-MedFiLM-Seg++.

Supported Task IDs:
  0: ISIC (dermatology / skin lesion)
  1: BUSI (breast ultrasound / breast lesion)
  2: Kvasir-SEG (gastrointestinal endoscopy / polyp)
  3: KUB-StoneX (urinary radiography / stone)
"""
from pathlib import Path

from .kub_predict import predict_kub

TASK_ID_MAP = {
    0: "ISIC",
    1: "BUSI",
    2: "KVASIR",
    3: "KUB",
    "0": "ISIC",
    "1": "BUSI",
    "2": "KVASIR",
    "3": "KUB",
    "ISIC": "ISIC",
    "BUSI": "BUSI",
    "KVASIR": "KVASIR",
    "KVASIR-SEG": "KVASIR",
    "KUB": "KUB",
    "KUB-STONEX": "KUB",
}


def predict(
    image_path,
    task="auto",
    model_name="unetpp",
    checkpoint_path=None,
    threshold=0.5,
    device=None,
    return_original_space=True,
    save_dir=None,
):
    """Unified entrypoint for medical image segmentation and automatic domain routing.

    In the current Phase 11 state:
    - task='auto' raises NotImplementedError (auto domain routing is reserved for the unified RA-MedFiLM-Seg++ phase).
    - task='KUB' delegates to predict_kub(...).
    - task='ISIC'/'BUSI'/'Kvasir' raises NotImplementedError.
    """
    if str(task).lower() == "auto":
        raise NotImplementedError(
            "Automatic four-domain routing is reserved for the unified "
            "RA-MedFiLM-Seg++ phase and is not yet scientifically validated."
        )

    task_key = TASK_ID_MAP.get(str(task).upper() if isinstance(task, str) else task)
    if task_key == "KUB":
        return predict_kub(
            image_path=image_path,
            model_name=model_name,
            checkpoint_path=checkpoint_path,
            threshold=threshold,
            device=device,
            return_original_space=return_original_space,
            save_dir=save_dir,
        )
    elif task_key in {"ISIC", "BUSI", "KVASIR"}:
        raise NotImplementedError(
            f"Task {task!r} ({task_key}) is reserved for the unified multi-domain "
            "phase and is not yet trained/validated."
        )
    else:
        raise ValueError(
            f"Unsupported task {task!r}. Supported task specifiers: 'auto', 'KUB', 'ISIC', 'BUSI', 'Kvasir' (or task IDs 0-3)."
        )
