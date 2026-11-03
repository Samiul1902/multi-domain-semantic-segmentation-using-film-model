"""BARR model components (Phase 25+)."""
from .phase25_models import (
    BARRBenefitRouterV1,
    BARRPostSafetyV1,
    ROUTER_EXPECTED_PARAMETERS,
    SAFETY_EXPECTED_PARAMETERS,
    architecture_fingerprint,
    count_trainable_parameters,
)
from .regional_refiner import (
    BARRRegionalRefinerV1,
    BARR_REFINER_ARCHITECTURE_ID,
    BARR_REFINER_CHANNELS,
    BARR_REFINER_EXPECTED_PARAMETERS,
    BARR_REFINER_HARD_CEILING,
    BARR_REFINER_INPUT_CHANNELS,
    BARR_REFINER_INPUT_RESOLUTION,
    BARR_REFINER_OUTPUT_CHANNELS,
    closed_form_parameter_count,
    count_parameters,
    assert_no_forbidden_modules,
    group_count,
)

__all__ = [
    "BARRBenefitRouterV1",
    "BARRPostSafetyV1",
    "ROUTER_EXPECTED_PARAMETERS",
    "SAFETY_EXPECTED_PARAMETERS",
    "architecture_fingerprint",
    "count_trainable_parameters",
    "BARRRegionalRefinerV1",
    "BARR_REFINER_ARCHITECTURE_ID",
    "BARR_REFINER_CHANNELS",
    "BARR_REFINER_EXPECTED_PARAMETERS",
    "BARR_REFINER_HARD_CEILING",
    "BARR_REFINER_INPUT_CHANNELS",
    "BARR_REFINER_INPUT_RESOLUTION",
    "BARR_REFINER_OUTPUT_CHANNELS",
    "closed_form_parameter_count",
    "count_parameters",
    "assert_no_forbidden_modules",
    "group_count",
]
