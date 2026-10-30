#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.2 shared execution semantics (frozen constants + synthetic builders).

Classification: PRE_MEASUREMENT_EXECUTABLE_HARNESS_AND_SYNTHETIC_TASK_CONDITIONING_
                BINDING_AMENDMENT__SHARED_SEMANTICS
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_2

This module contains NO model construction, NO checkpoint loading, NO forward execution
and NO timing. It only defines frozen constants and deterministic synthetic-tensor
builders. Importing it never touches a checkpoint or the GPU allocator.

Authority for the domain -> task_id registry:
  src/analysis/multidomain_harmonization.py  TASK_ID = {"ISIC":0,"BUSI":1,"KVASIR":2,"KUB":3}
  reports/tables/phase25f_feature_schema_v1_0.csv  indices 16..19 = task one-hot
  reports/audits/phase30_system_under_test_contract.json
"""
from __future__ import annotations

from collections import OrderedDict

# --------------------------------------------------------------------------- #
# domain -> task_id registry (frozen)
# --------------------------------------------------------------------------- #
DOMAIN_TASK_ID = OrderedDict([("ISIC", 0), ("BUSI", 1), ("KVASIR", 2), ("KUB", 3)])
TASK_ID_DOMAIN = {v: k for k, v in DOMAIN_TASK_ID.items()}
TASK_ORDER = [0, 1, 2, 3]                      # ISIC, BUSI, KVASIR, KUB
BATCH8_TASK_VECTOR = [0, 1, 2, 3, 0, 1, 2, 3]  # exactly balanced four-domain batch
TASK_COUNT = 4

# --------------------------------------------------------------------------- #
# frozen timing protocol (unchanged from v1.1 accepted contracts)
# --------------------------------------------------------------------------- #
PRIMARY_LATENCY_BATCH_SIZE = 1
SECONDARY_THROUGHPUT_BATCH_SIZE = 8
WARMUP_ITERATIONS = 50
MEASUREMENT_BLOCKS = 5
MEASURED_ITERATIONS_PER_BLOCK = 200
TOTAL_MEASURED_ITERATIONS = MEASUREMENT_BLOCKS * MEASURED_ITERATIONS_PER_BLOCK  # 1000
TASK_CONDITIONS_PER_TASK_ID = TOTAL_MEASURED_ITERATIONS // TASK_COUNT           # 250

# --------------------------------------------------------------------------- #
# numeric synthetic generator (frozen terminology)
# --------------------------------------------------------------------------- #
GENERATOR_SEMANTICS = "PYTORCH_CUDA_GENERATOR_SEED_42"
SYNTHETIC_SEED = 42


def make_generator(device: str = "cuda"):
    """Exactly: torch.Generator(device="cuda").manual_seed(42)."""
    import torch
    return torch.Generator(device=device).manual_seed(SYNTHETIC_SEED)


def task_id_for_iteration(iteration_index: int) -> int:
    """Batch-1 task schedule: task_id(iteration_index) = iteration_index mod 4."""
    return int(iteration_index) % TASK_COUNT


# --------------------------------------------------------------------------- #
# canonical component registry (checkpoint + class + geometry)
# --------------------------------------------------------------------------- #
COMPONENTS = OrderedDict([
    ("G", OrderedDict([
        ("model_class", "GlobalMedFiLM"),
        ("source_file", "src/models/film/global_medfilm.py"),
        ("config_file", "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"),
        ("checkpoint", "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"),
        ("checkpoint_sha256",
         "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
        ("expected_parameters", 3523001),
        ("state_dict_key", "model_state"),
        ("image_shape", [None, 3, 512, 512]),
        ("task_conditioning", "INTEGER_TASK_ID_FILM_EMBEDDING"),
        ("autocast_enabled", True), ("autocast_dtype", "float16"),
        ("grad_context", "torch.no_grad()"), ("inference_mode", False),
    ])),
    ("R_psi", OrderedDict([
        ("model_class", "BARRRegionalRefinerV1"),
        ("source_file", "src/models/barr/regional_refiner.py"),
        ("checkpoint", "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt"),
        ("checkpoint_sha256",
         "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"),
        ("expected_parameters", 1276401),
        ("state_dict_key", "model_state"),
        ("input_shape", [None, 4, 256, 256]),
        ("task_conditioning", "NONE"),
        ("autocast_enabled", False), ("autocast_dtype", None),
        ("grad_context", "torch.inference_mode()"), ("inference_mode", True),
    ])),
    ("B_phi", OrderedDict([
        ("model_class", "BARRBenefitRouterV1"),
        ("source_file", "scripts/analysis/train_phase25d_router.py"),
        ("checkpoint", "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt"),
        ("checkpoint_sha256",
         "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
        ("expected_parameters", 36801),
        ("state_dict_key", "model_state"),
        ("numeric_feature_dim", 202),
        ("task_conditioning", "INTEGER_TASK_ID_EMBEDDING"),
        ("normalized_scalar_indices", [192, 193, 194, 195, 196, 197, 200, 201]),
        ("autocast_enabled", False), ("autocast_dtype", None),
        ("grad_context", "torch.inference_mode()"), ("inference_mode", True),
    ])),
    ("S_omega", OrderedDict([
        ("model_class", "BARRPostSafetyV1"),
        ("source_file", "scripts/analysis/phase25f_execution_common.py"),
        ("checkpoint", "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"),
        ("checkpoint_sha256",
         "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"),
        ("expected_parameters", 1217),
        ("state_dict_key", "model_state"),
        ("feature_dim", 20),
        ("numeric_indices", list(range(0, 16))),
        ("onehot_indices", list(range(16, 20))),
        ("task_conditioning", "STRUCTURED_TASK_ONE_HOT_TAIL_16_19"),
        ("autocast_enabled", False), ("autocast_dtype", None),
        ("grad_context", "torch.inference_mode()"), ("inference_mode", True),
    ])),
])

TOTAL_RESIDENT_PARAMETERS = sum(c["expected_parameters"] for c in COMPONENTS.values())

# --------------------------------------------------------------------------- #
# frozen runtime arms
# --------------------------------------------------------------------------- #
ARMS = OrderedDict([
    ("GLOBAL_ONLY_C1", {"components": ["G"], "kind": "path"}),
    ("FINAL_ROUTED_A8_C9", {"components": ["G", "B_phi", "R_psi", "S_omega"],
                            "kind": "controlled_path"}),
    ("SKIP_CONTROLLED_PATH", {"components": ["G", "B_phi"], "kind": "controlled_path"}),
    ("EXECUTE_CONTROLLED_PATH", {"components": ["G", "B_phi", "R_psi", "S_omega"],
                                 "kind": "controlled_path"}),
    ("G_COMPONENT", {"components": ["G"], "kind": "component"}),
    ("R_PSI_COMPONENT", {"components": ["R_psi"], "kind": "component"}),
    ("B_PHI_COMPONENT", {"components": ["B_phi"], "kind": "component"}),
    ("S_OMEGA_COMPONENT", {"components": ["S_omega"], "kind": "component"}),
])

ANALYTICAL_ONLY_ARMS = ["LITERAL_ALWAYS_REFINE_C2", "GATED_EXECUTE_ALL_C9"]

BATCH1_LABEL = ("CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_"
                "NUMERICAL_REPRODUCTION")
BATCH8_LABEL = "SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK"

# --------------------------------------------------------------------------- #
# timed-operation registry (machine readable)
# --------------------------------------------------------------------------- #
TIMED_OPERATIONS = OrderedDict([
    ("GLOBAL_ONLY_C1", OrderedDict([
        ("included_operations", ["G model forward", "G sigmoid"]),
        ("excluded_operations", ["feature normalization", "router feature construction",
                                 "ROI geometry", "crop/resizing", "interpolation", "fusion",
                                 "decision logic", "host-to-device transfer",
                                 "device-to-host transfer", "checkpoint loading",
                                 "synthetic tensor generation"]),
        ("input_tensors_preconstructed", True), ("host_device_transfer_included", False),
        ("checkpoint_load_included", False), ("roi_geometry_included", False),
        ("crop_resize_included", False), ("fusion_included", False),
        ("decision_logic_included", False),
        ("scope", "MODEL_COMPUTE_PATH_RUNTIME"),
    ])),
    ("FINAL_ROUTED_A8_C9", OrderedDict([
        ("included_operations", ["G model forward", "G sigmoid", "B_phi model forward",
                                 "R_psi model forward", "R_psi sigmoid",
                                 "S_omega model forward"]),
        ("excluded_operations", ["feature normalization", "router feature construction",
                                 "ROI geometry", "crop/resizing", "interpolation", "fusion",
                                 "decision logic", "host-to-device transfer",
                                 "device-to-host transfer", "checkpoint loading",
                                 "synthetic tensor generation"]),
        ("input_tensors_preconstructed", True), ("host_device_transfer_included", False),
        ("checkpoint_load_included", False), ("roi_geometry_included", False),
        ("crop_resize_included", False), ("fusion_included", False),
        ("decision_logic_included", False),
        ("scope", "MODEL_COMPUTE_PATH_RUNTIME"),
    ])),
    ("SKIP_CONTROLLED_PATH", OrderedDict([
        ("included_operations", ["G model forward", "G sigmoid", "B_phi model forward"]),
        ("excluded_operations", ["R_psi model forward", "S_omega model forward",
                                 "feature normalization", "router feature construction",
                                 "ROI geometry", "crop/resizing", "interpolation", "fusion",
                                 "decision logic", "host-to-device transfer",
                                 "device-to-host transfer", "checkpoint loading",
                                 "synthetic tensor generation"]),
        ("input_tensors_preconstructed", True), ("host_device_transfer_included", False),
        ("checkpoint_load_included", False), ("roi_geometry_included", False),
        ("crop_resize_included", False), ("fusion_included", False),
        ("decision_logic_included", False),
        ("scope", "MODEL_COMPUTE_PATH_RUNTIME"),
    ])),
    ("EXECUTE_CONTROLLED_PATH", OrderedDict([
        ("included_operations", ["G model forward", "G sigmoid", "B_phi model forward",
                                 "R_psi model forward", "R_psi sigmoid",
                                 "S_omega model forward"]),
        ("excluded_operations", ["feature normalization", "router feature construction",
                                 "ROI geometry", "crop/resizing", "interpolation", "fusion",
                                 "decision logic", "host-to-device transfer",
                                 "device-to-host transfer", "checkpoint loading",
                                 "synthetic tensor generation"]),
        ("input_tensors_preconstructed", True), ("host_device_transfer_included", False),
        ("checkpoint_load_included", False), ("roi_geometry_included", False),
        ("crop_resize_included", False), ("fusion_included", False),
        ("decision_logic_included", False),
        ("scope", "MODEL_COMPUTE_PATH_RUNTIME"),
    ])),
])
for _c in ("G_COMPONENT", "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT"):
    TIMED_OPERATIONS[_c] = OrderedDict([
        ("included_operations", ["component model forward", "component sigmoid (where "
                                 "applicable)"]),
        ("excluded_operations", ["all other components", "feature normalization",
                                 "ROI geometry", "crop/resizing", "interpolation", "fusion",
                                 "decision logic", "host-to-device transfer",
                                 "device-to-host transfer", "checkpoint loading",
                                 "synthetic tensor generation"]),
        ("input_tensors_preconstructed", True), ("host_device_transfer_included", False),
        ("checkpoint_load_included", False), ("roi_geometry_included", False),
        ("crop_resize_included", False), ("fusion_included", False),
        ("decision_logic_included", False),
        ("scope", "SYNTHETIC_COMPONENT_RUNTIME"),
    ])

# --------------------------------------------------------------------------- #
# deterministic synthetic input builders (no checkpoint, no model)
# --------------------------------------------------------------------------- #
def build_G_image(batch_size: int, device: str = "cuda"):
    import torch
    g = make_generator(device)
    return torch.randn(batch_size, 3, 512, 512, generator=g, device=device,
                       dtype=torch.float32)


def build_G_task_ids(batch_size: int, start_index: int = 0, device: str = "cuda"):
    """int64 [B] task ids following the frozen schedule."""
    import torch
    if batch_size == SECONDARY_THROUGHPUT_BATCH_SIZE:
        ids = BATCH8_TASK_VECTOR
    else:
        ids = [task_id_for_iteration(start_index + i) for i in range(batch_size)]
    return torch.tensor(ids, dtype=torch.long, device=device)


def build_Rpsi_input(batch_size: int, device: str = "cuda"):
    import torch
    g = make_generator(device)
    return torch.randn(batch_size, 4, 256, 256, generator=g, device=device,
                       dtype=torch.float32)


def build_Bphi_features(batch_size: int, device: str = "cuda"):
    """202-D numeric router features (no categorical fields; task signal is a separate id)."""
    import torch
    g = make_generator(device)
    return torch.randn(batch_size, 202, generator=g, device=device, dtype=torch.float32)


def build_Somega_features(batch_size: int, start_index: int = 0, device: str = "cuda"):
    """16 deterministic numeric dims + a STRUCTURED one-hot tail at indices 16..19."""
    import torch
    g = make_generator(device)
    numeric = torch.randn(batch_size, 16, generator=g, device=device, dtype=torch.float32)
    if batch_size == SECONDARY_THROUGHPUT_BATCH_SIZE:
        ids = BATCH8_TASK_VECTOR
    else:
        ids = [task_id_for_iteration(start_index + i) for i in range(batch_size)]
    onehot = torch.zeros(batch_size, 4, device=device, dtype=torch.float32)
    for r, t in enumerate(ids):
        onehot[r, int(t)] = 1.0
    return torch.cat([numeric, onehot], dim=1)
