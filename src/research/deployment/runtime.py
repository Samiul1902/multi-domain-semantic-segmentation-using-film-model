"""Reuse the production FULL loader and GT-free adapter for a verified package."""
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import torch

from src.data.transforms import SegmentationTransform
from src.research.full_pipeline.inference import FamilyBundle
from .artifacts import ArtifactError, digest, verify


class FullPackageRuntime:
    """No filesystem image reader: only explicitly supplied images and task IDs."""

    def __init__(self, root: Path, expected_manifest_sha256: str, *, device: str = "cpu"):
        self.manifest = verify(root, expected_manifest_sha256)
        config = self.manifest["config"]
        if config["family"] != "FULL":
            raise ArtifactError("this runtime requires a FULL package")
        import inspect
        if digest(Path(inspect.getfile(SegmentationTransform))) != config["preprocessing"]["implementation_sha256"]:
            raise ArtifactError("preprocessing implementation differs from package")
        if digest(Path(inspect.getfile(FamilyBundle))) != config["source_sha256"]:
            raise ArtifactError("loader implementation differs from package")
        context = SimpleNamespace(seed=config["seed"], tag="verified-package")
        self.bundle = FamilyBundle.load(context, checkpoint_paths={
            c: Path(root) / "components" / f"{c}.pt" for c in "GRBS"})
        self.engine = self.bundle.build_gtfree(device=device)
        self.transform = SegmentationTransform(size=512, train=False, image_mode="RGB")

    def infer(self, image: torch.Tensor, task_id: int) -> dict:
        if tuple(image.shape) != (1, 3, 512, 512) or type(task_id) is not int or task_id not in range(4):
            raise ArtifactError("expected one RGB 512 control tensor and a task ID in 0..3")
        if not torch.isfinite(image).all() or image.min() < 0 or image.max() > 1:
            raise ArtifactError("invalid image values")
        return self.engine.infer(image, task_id)

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        tensor, _, _ = self.transform(image, Image.new("L", image.size, 0))
        return tensor.unsqueeze(0)
