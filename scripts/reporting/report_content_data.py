"""
report_content_data.py
======================
Frozen, provenance-bound content for the RA-MedFiLM-BARR Full Supervisor Report.

DOCUMENT ASSEMBLY ONLY.  Every number and claim in this module is transcribed
verbatim from the frozen release artifacts listed in the source hierarchy:

  reports/manuscript/final/final_number_provenance.json
  reports/manuscript/final/final_claim_ledger.json
  reports/manuscript/final/final_table_registry.json
  reports/manuscript/final/final_figure_registry.json
  reports/manuscript/final/manuscript_final.md (+ abstract/methods/results/
                                                discussion/limitations/supplement)
  reports/tables/phase37_consolidated/*.csv
  reports/manuscript/phase40/tables/phase39_descriptive_TEST_table.csv
  reports/audits/final_manuscript_*.json
  reports/figures/methodology_diagram_package/methodology_diagram_manifest.json
  reports/figures/methodology_diagram_package/thresholds_and_decisions.json

scientific_delta = 0.  No new value was computed, inferred, or invented here.
Where a field is not frozen, this module records the literal token
"Not reported / not applicable".
"""

# ---------------------------------------------------------------------------
# Release identity (verified before build)
# ---------------------------------------------------------------------------
RELEASE = {
    "manuscript_final_path": "reports/manuscript/final/manuscript_final.md",
    "manuscript_final_sha256": "757cb73d419c224909e884b610d69d3fe62da5c33d9cb63115789179da9935a4",
    "release_manifest_path": "reports/audits/final_manuscript_sha256_manifest.json",
    "release_manifest_sha256": "2a4b1f92b2ea384bd1adec976ee1a364a015ee5f9fc14c3f5cfd6e9c47781e3f",
    "final_scientific_scope": "MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY",
    "scientific_delta": 0,
}

NOT_REPORTED = "Not reported / not applicable"

# Verbatim qualifiers that MUST appear.
PHASE30_QUALIFIER = (
    "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_"
    "POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION"
)
PHASE39_EVIDENCE_CLASS = (
    "POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_"
    "TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES"
)

# ---------------------------------------------------------------------------
# SECTION 6 — datasets and tasks
# ---------------------------------------------------------------------------
TASKS = [
    ("Task 0", "ISIC", "RGB dermoscopy", "3-channel RGB", "Binary foreground / background"),
    ("Task 1", "BUSI", "Ultrasound", "L -> RGB", "Binary foreground / background"),
    ("Task 2", "KVASIR", "RGB endoscopy", "3-channel RGB", "Binary foreground / background"),
    ("Task 3", "KUB", "Radiograph", "L / RGB", "Binary foreground / background"),
]

POPULATION_SPLITS = [
    ("TRAIN", "5,832", "ISIC 2,556 / BUSI 602 / KVASIR 696 / KUB 1,978", "Development training set"),
    ("VAL808", "808", "ISIC 357 / BUSI 84 / KVASIR 87 / KUB 280", "Frozen development / validation set (Phase27)"),
    ("ROUTER_DEVELOPMENT", "4,957", "Budget K = 1,239 routed rows", "Ablation / reproducibility development population (Phase28/29)"),
    ("ROUTER_HOLDOUT", "875", "BUSI 90 / ISIC 383 / KUB 298 / KVASIR 104", "One-shot held-out evaluation (Phase30)"),
    ("TEST", "1,683", "ISIC 735 / BUSI 174 / KVASIR 216 / KUB 558", "Final descriptive evaluation cohort (Phase39 v1.2)"),
]

TEST_DOMAIN_TABLE = [
    ("ISIC", "735", "0.88693", "PRESENT"),
    ("BUSI", "174", "0.85042", "PRESENT"),
    ("KVASIR", "216", "0.85071", "PRESENT"),
    ("KUB", "558", "0.73769", "PRESENT"),
    ("MACRO (macro-domain Dice)", "1,683", "0.8314368385956257", "PRESENT"),
    ("macro DeltaDice vs C-gGLOBAL", "-", "NOT_PRODUCED_BY_FROZEN_PHASE39_EXECUTION", "NOT_PRODUCED"),
    ("comparative confidence interval", "-", "NOT_PRODUCED_BY_FROZEN_PHASE39_EXECUTION", "NOT_PRODUCED"),
    ("per-domain harm flag", "-", "NOT_PRODUCED_BY_FROZEN_PHASE39_EXECUTION", "NOT_PRODUCED"),
]

KUB_SUBGROUPS = [
    ("Kidney_Stone", "112", "REPORTING-ONLY metadata"),
    ("Bladder_Stone", "144", "REPORTING-ONLY metadata"),
    ("Ureteric_Stone", "24", "REPORTING-ONLY metadata"),
]

# ---------------------------------------------------------------------------
# SECTION 8 — final architecture / components
# ---------------------------------------------------------------------------
ARCH_TABLE = [
    ("G", "GlobalMedFiLM", "3,523,001", "Always executed",
     "always executed"),
    ("B_phi", "BARRBenefitRouterV1", "36,801", "202-D features + task embedding",
     "pre-gate (always executed)"),
    ("R_psi", "BARRRegionalRefinerV1", "1,276,401", "[B,4,256,256] ROI crop",
     "EXECUTE branch only"),
    ("S_omega", "BARRPostSafetyV1", "1,217", "16-D numeric + 4-D task one-hot",
     "EXECUTE branch only"),
    ("--", "RAMedFiLMBARR (assembly wrapper)", "0 trainable", "assembly only",
     "assembly only"),
]

ARCH_COMPONENT_SPEC = [
    ("G", "3523001", "42369710",
     "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
     "always executed"),
    ("R_psi", "1276401", "15425424",
     "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
     "EXECUTE branch only"),
    ("B_phi", "36801", "455682",
     "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
     "pre-gate (always executed)"),
    ("S_omega", "1217", "7816",
     "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
     "EXECUTE branch only"),
]

CHECKPOINT_IDENTITIES = [
    ("G", "GlobalMedFiLM",
     "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
     "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
    ("B_phi", "BARRBenefitRouterV1",
     "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
     "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
    ("R_psi", "BARRRegionalRefinerV1",
     "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
     "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"),
    ("S_omega", "BARRPostSafetyV1",
     "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
     "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"),
]

# ---------------------------------------------------------------------------
# SECTION 14 — state machine
# ---------------------------------------------------------------------------
STATE_MACHINE = [
    ("FORCED_SKIP",
     "ROI proposal empty (ACTION_UNAVAILABLE)",
     "No", "No",
     "Global prediction",
     "Global prediction is emitted unchanged; router/refiner/safety never invoked."),
    ("SKIP_GLOBAL",
     "Router gate decided SKIP (U < tau_C8_final)",
     "No", "No",
     "Global prediction",
     "Benefit expected to be low; global prediction is the final output."),
    ("EXECUTE_THEN_ACCEPT",
     "Router decided EXECUTE and S_omega accepted (>= 0.50)",
     "Yes", "Yes",
     "Fused (D61 pad-aware) prediction",
     "Refinement judged safe; pad-aware fusion of the refined region is emitted."),
    ("EXECUTE_THEN_REJECT",
     "Router decided EXECUTE and S_omega rejected (< 0.50)",
     "Yes", "Yes",
     "Global prediction (fallback)",
     "Refinement ran but was not accepted; the global prediction is restored."),
]

# ---------------------------------------------------------------------------
# SECTION 17 — development / preservation results
# ---------------------------------------------------------------------------
VAL808_PER_DOMAIN = [
    ("BUSI", "84", "0.8588214375680574", "0.8589126018391846", "0.000091", "0.000000", "0.000273", "No harm flag"),
    ("ISIC", "357", "0.8971889499163059", "0.8980801299180301", "0.000891", "-0.000211", "0.002032", "No harm flag"),
    ("KUB", "280", "0.7640588414471431", "0.771512927778779", "0.007454", "0.004550", "0.010114", "No harm flag"),
    ("KVASIR", "87", "0.8202466114984852", "0.8206507619743234", "0.000404", "-0.002362", "0.003744", "No harm flag"),
    ("MACRO", "808", "--", "--", "0.002210", "0.001133", "0.003298", "No harm flag"),
]

VAL808_HOLDOUT_DELTA = [
    ("BUSI", "0.000005152", "0.000000", "0.0000155"),
    ("ISIC", "0.000986291", "0.000328887", "0.001764382"),
    ("KUB", "0.005944727", "0.003634999", "0.008455643"),
    ("KVASIR", "0.000019953", "0.000000", "0.0000599"),
    ("MACRO", "0.001739031", "0.001117294", "0.002404981"),
]

# ---------------------------------------------------------------------------
# SECTION 18 — ablation
# ---------------------------------------------------------------------------
ABLATION_TABLE = [
    ("A0", "0", "0.0000", "0.000000", "0.000", "0", "0", "0.000", "ENDPOINT_BY_CONSTRUCTION"),
    ("A1", "4957", "1.0000", "0.001658", "1.000", "2775", "2115", "0.427", "ENDPOINT_BY_CONSTRUCTION"),
    ("A2", "1239", "0.2499", "0.001413", "0.246", "669", "550", "0.444", "PRIOR_CANONICAL_EVIDENCE_EXACT"),
    ("A3", "1239", "0.2499", "0.007185", "0.584", "844", "395", "0.319", "PRIOR_CANONICAL_EVIDENCE_EXACT"),
    ("A4", "1239", "0.2499", "0.007119", "0.582", "843", "396", "0.320", "PRIOR_CANONICAL_EVIDENCE_EXACT"),
    ("A5", "1239", "0.2499", "-0.000433", "0.184", "597", "575", "0.464", "PRIOR_CANONICAL_EVIDENCE_EXACT"),
    ("A6", "1239", "0.2499", "0.007247", "0.602", "827", "412", "0.333", "PRIOR_CANONICAL_EVIDENCE_EXACT"),
    ("A7", "1239", "0.2499", "0.007247", "0.602", "827", "412", "0.333", "PRIOR_CANONICAL_EVIDENCE_EXACT"),
    ("A8", "1205", "0.2431", "0.007516", "0.597", "815", "390", "0.324", "PRIOR_CANONICAL_EVIDENCE_EXACT"),
    ("R1", "1239", "0.2499", "0.003320", "0.495", "723", "463", "0.374", "PHASE28_TRAINED_ABLATION_VARIANT"),
    ("R2", "1239", "0.2499", "0.001191", "0.246", "678", "539", "0.435", "PHASE28_TRAINED_ABLATION_VARIANT"),
    ("R3", "1239", "0.2499", "0.001251", "0.244", "702", "524", "0.423", "PHASE28_TRAINED_ABLATION_VARIANT"),
    ("F1", "1239", "0.2499", "-0.032585", "0.283", "256", "853", "0.688", "PHASE28_TRAINED_ABLATION_VARIANT"),
]

# ---------------------------------------------------------------------------
# SECTION 19 — reproducibility
# ---------------------------------------------------------------------------
REPRO_TABLE = [
    ("ROUTER_DEVELOPMENT", "macro_domain_final_dice", "0.9304901760", "0.9303465583", "0.9303620955", "0.9303996099", "True"),
    ("ROUTER_DEVELOPMENT", "macro_domain_delta_dice", "0.0013053961", "0.0011617784", "0.0011773155", "0.0012148300", "True"),
    ("ROUTER_DEVELOPMENT", "routed_candidate_mean_delta_dice", "0.0072466292", "0.0065878388", "0.0066232275", "0.0068192318", "True"),
    ("ROUTER_DEVELOPMENT", "benefit_capture", "0.6021987300", "0.5603838551", "0.5869805243", "0.5831877031", "True"),
    ("ROUTER_DEVELOPMENT", "harmful_activation_share", "0.1081517353", "0.1242937853", "0.1420500404", "0.1248318536", "True"),
    ("ROUTER_DEVELOPMENT", "safety_accept_fraction", "0.9725585149", "0.8555286521", "0.9539951574", "0.9273607748", "True"),
    ("ROUTER_DEVELOPMENT", "n_selected", "1239", "1239", "1239", "1239.0", "NA"),
    ("VAL808_PHASE_D", "macro_final_dice", "0.8372891054", "0.8384669007", "0.8379477614", "0.8379012558", "True"),
    ("VAL808_PHASE_D", "macro_global_dice", "0.8350789601", "0.8350789601", "0.8350789601", "0.8350789601", "True"),
    ("VAL808_PHASE_D", "macro_delta_dice", "0.0022101453", "0.0033879406", "0.0028688013", "0.0028222957", "True"),
    ("VAL808_PHASE_D", "selected_fraction", "0.3452970297", "0.3155940594", "0.3242574257", "0.3283828383", "True"),
    ("VAL808_PHASE_D", "safety_accept_fraction", "0.9534050179", "0.9019607843", "0.9770992366", "0.9441550130", "True"),
]

# ---------------------------------------------------------------------------
# SECTION 20 — ROUTER_HOLDOUT
# ---------------------------------------------------------------------------
HOLDOUT_TABLE = [
    ("Final system (A8/C9) macro Dice", "0.9302871820357663"),
    ("Global reference macro Dice", "0.9285481511747413"),
    ("Macro DeltaDice", "0.0017390308610248934"),
    ("95% domain-stratified bootstrap CI", "[0.00111729355352301, 0.0024049809029647283]"),
]

# ---------------------------------------------------------------------------
# SECTION 22 — failure modes
# ---------------------------------------------------------------------------
FAILURE_TABLE = [
    ("LOW_OVERLAP", "875", "88", "0.10057142857142858", "All 875 ROUTER_HOLDOUT rows"),
    ("EMPTY_PREDICTION", "875", "0", "0.0", "All 875 ROUTER_HOLDOUT rows"),
    ("ROUTER_HARMFUL_ACTIVATION", "240", "31", "0.12916666666666668", "EXECUTE rows (240)"),
    ("ROUTER_MISSED_BENEFIT", "635", "0", "0.0", "SKIP rows (635)"),
    ("EXECUTE_THEN_REJECT", "240", "4", "0.016666666666666666", "EXECUTE rows (240)"),
]

FAILURE_BY_DOMAIN = (
    "BUSI n=90 / ISIC n=383 / KUB n=298 / KVASIR n=104; "
    "KUB highest low-overlap (0.2450) and harmful-activation (0.0872)"
)

# ---------------------------------------------------------------------------
# SECTION 23 — efficiency
# ---------------------------------------------------------------------------
EFFICIENCY_TABLE = [
    ("A8/C9 expected analytical MAC lower bound", "32437902022.582855", "MACs",
     "ANALYTICAL_MAC_LOWER_BOUND"),
    ("Analytical MAC ratio vs global-only (C1)", "1.0280859651011032", "ratio",
     "ANALYTICAL_RATIO"),
    ("Analytical MAC saving vs always-refine (C2)", "2344501561.417145", "MACs",
     "ANALYTICAL_SAVING_MACS"),
    ("Measured latency - SKIP path (batch-1, v1.4)", "15.71835146522522", "ms",
     "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE"),
    ("Measured latency - EXECUTE path (batch-1, v1.4)", "18.894091419219972", "ms",
     "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE"),
    ("Measured latency - weighted (p_SKIP=0.7257, p_EXECUTE=0.2743)",
     "16.589411566892352", "ms", "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE"),
    ("Measured throughput - SKIP path (batch-8)", "93.17560442781323", "samples/s",
     "MODEL_COMPUTE_PATH_RUNTIME"),
    ("Measured throughput - EXECUTE path (batch-8)", "80.26287810203608", "samples/s",
     "MODEL_COMPUTE_PATH_RUNTIME"),
    ("GPU peak allocated - SKIP path", "336239104", "bytes", "GPU_MEMORY"),
    ("GPU peak allocated - EXECUTE path", "345559552", "bytes", "GPU_MEMORY"),
    ("Total parameters (G+R_psi+B_phi+S_omega)", "4837420", "parameters",
     "STATIC_MODEL_RESOURCE_PROFILE"),
]

# ---------------------------------------------------------------------------
# SECTION 24 — interpretability / routing
# ---------------------------------------------------------------------------
INTERP_GROUP_ATTRIBUTION = [
    ("bridge_global", "0.7022336934747089", "0.018495175385098966"),
    ("bridge_roi", "0.7230366555447487", "0.019043076227212012"),
    ("decoder2_global", "7.10764316959649", "0.1871985184104845"),
    ("decoder2_roi", "5.460231437830695", "0.1438095879253719"),
    ("decoder1_global", "12.301891267383665", "0.3240027339515185"),
    ("decoder1_roi", "11.673443601480157", "0.30745090810031406"),
]

INTERP_SALIENCY = [
    ("bridge | ISIC", "0.21552787398104556", "0.06956793181598186"),
    ("bridge | BUSI", "0.17095443938160315", "0.054967453703284264"),
    ("bridge | KVASIR", "0.3127893512719311", "0.13337256759405136"),
    ("bridge | KUB", "0.20097172392269158", "0.0034866328714997508"),
    ("decoder1 | ISIC", "0.9999990127980709", "1.0"),
    ("decoder1 | BUSI", "0.9999999664723873", "1.0"),
    ("decoder1 | KVASIR", "0.9999996721744537", "1.0"),
    ("decoder1 | KUB", "0.9999994933605194", "1.0"),
]

# ---------------------------------------------------------------------------
# SECTION 25 — robustness
# ---------------------------------------------------------------------------
IMAGE_ROBUSTNESS_TABLE = [
    ("BUSI", "BRIGHTNESS_NEG", "84", "-0.005977", "0.000436"),
    ("ISIC", "BRIGHTNESS_NEG", "357", "-0.000858", "-0.000594"),
    ("KUB", "BRIGHTNESS_NEG", "280", "-0.016720", "0.000000"),
    ("KVASIR", "BRIGHTNESS_NEG", "87", "-0.007922", "-0.001392"),
    ("BUSI", "BRIGHTNESS_POS", "84", "-0.004116", "-0.001763"),
    ("ISIC", "BRIGHTNESS_POS", "357", "-0.004450", "-0.000359"),
    ("KUB", "BRIGHTNESS_POS", "280", "-0.008172", "0.000000"),
    ("KVASIR", "BRIGHTNESS_POS", "87", "-0.009699", "-0.001401"),
    ("BUSI", "CONTRAST_LOW", "84", "-0.002394", "-0.001151"),
    ("ISIC", "CONTRAST_LOW", "357", "-0.005262", "-0.001289"),
    ("KUB", "CONTRAST_LOW", "280", "-0.004774", "-0.000222"),
    ("KVASIR", "CONTRAST_LOW", "87", "-0.000549", "-0.000707"),
    ("BUSI", "CONTRAST_HIGH", "84", "-0.0000341", "0.000212"),
    ("ISIC", "CONTRAST_HIGH", "357", "0.000572", "0.000282"),
    ("KUB", "CONTRAST_HIGH", "280", "-0.001432", "-0.0000795"),
    ("KVASIR", "CONTRAST_HIGH", "87", "-0.003817", "-0.000319"),
    ("BUSI", "GAMMA_LOW", "84", "-0.012725", "-0.003971"),
    ("ISIC", "GAMMA_LOW", "357", "-0.002545", "-0.000336"),
    ("KUB", "GAMMA_LOW", "280", "-0.004263", "-0.001096"),
    ("KVASIR", "GAMMA_LOW", "87", "-0.009446", "-0.000470"),
    ("BUSI", "GAMMA_HIGH", "84", "-0.001724", "0.001546"),
    ("ISIC", "GAMMA_HIGH", "357", "-0.000507", "-0.000322"),
    ("KUB", "GAMMA_HIGH", "280", "-0.0000781", "1.21e-12"),
    ("KVASIR", "GAMMA_HIGH", "87", "-0.001462", "-0.000905"),
    ("BUSI", "GAUSSIAN_BLUR_LOW", "84", "0.000690", "0.000454"),
    ("ISIC", "GAUSSIAN_BLUR_LOW", "357", "-0.000708", "-0.000192"),
    ("KUB", "GAUSSIAN_BLUR_LOW", "280", "-0.005898", "0.000000"),
    ("KVASIR", "GAUSSIAN_BLUR_LOW", "87", "-0.001399", "-0.000366"),
    ("BUSI", "GAUSSIAN_BLUR_HIGH", "84", "-0.003057", "-0.000347"),
    ("ISIC", "GAUSSIAN_BLUR_HIGH", "357", "-0.004973", "-0.000672"),
    ("KUB", "GAUSSIAN_BLUR_HIGH", "280", "-0.056275", "-0.011809"),
    ("KVASIR", "GAUSSIAN_BLUR_HIGH", "87", "-0.014409", "-0.006818"),
    ("BUSI", "RESOLUTION_075", "84", "-0.001521", "0.001104"),
    ("ISIC", "RESOLUTION_075", "357", "-0.002164", "-0.000212"),
    ("KUB", "RESOLUTION_075", "280", "-0.034207", "-0.004405"),
    ("KVASIR", "RESOLUTION_075", "87", "-0.006006", "-0.001894"),
    ("BUSI", "RESOLUTION_050", "84", "-0.003723", "-0.001315"),
    ("ISIC", "RESOLUTION_050", "357", "-0.004636", "-0.000498"),
    ("KUB", "RESOLUTION_050", "280", "-0.054385", "-0.012256"),
    ("KVASIR", "RESOLUTION_050", "87", "-0.016622", "-0.007257"),
    ("BUSI", "GAUSSIAN_NOISE_LOW", "252", "-0.009229", "0.000279"),
    ("ISIC", "GAUSSIAN_NOISE_LOW", "1071", "-0.002824", "-0.000611"),
    ("KUB", "GAUSSIAN_NOISE_LOW", "840", "-0.115273", "-0.063727"),
    ("KVASIR", "GAUSSIAN_NOISE_LOW", "261", "-0.006576", "-0.001311"),
    ("BUSI", "GAUSSIAN_NOISE_HIGH", "252", "-0.089883", "-0.011001"),
    ("ISIC", "GAUSSIAN_NOISE_HIGH", "1071", "-0.031531", "-0.007134"),
    ("KUB", "GAUSSIAN_NOISE_HIGH", "840", "-0.363643", "-0.295749"),
    ("KVASIR", "GAUSSIAN_NOISE_HIGH", "261", "-0.060405", "-0.023059"),
]

PROPOSAL_ROBUSTNESS_TABLE = [
    ("BUSI", "SHIFT_LEFT_10", "84", "0.000202", "0.000000"),
    ("BUSI", "SHIFT_RIGHT_10", "84", "0.0000214", "0.000000"),
    ("BUSI", "SHIFT_UP_10", "84", "0.0000214", "0.000000"),
    ("BUSI", "SHIFT_DOWN_10", "84", "0.0000214", "0.000000"),
    ("BUSI", "SCALE_085", "84", "0.000903", "0.000000"),
    ("BUSI", "SCALE_115", "84", "0.0000214", "0.000000"),
    ("ISIC", "SHIFT_LEFT_10", "357", "-0.0000592", "0.000000"),
    ("ISIC", "SHIFT_RIGHT_10", "357", "-0.0000686", "0.000000"),
    ("ISIC", "SHIFT_UP_10", "357", "-0.000286", "0.000000"),
    ("ISIC", "SHIFT_DOWN_10", "357", "-0.0000021", "0.000000"),
    ("ISIC", "SCALE_085", "357", "-0.000408", "0.000000"),
    ("ISIC", "SCALE_115", "357", "-0.000387", "0.000000"),
    ("KUB", "SHIFT_LEFT_10", "280", "-0.000830", "0.000000"),
    ("KUB", "SHIFT_RIGHT_10", "280", "0.000131", "0.000000"),
    ("KUB", "SHIFT_UP_10", "280", "-0.000481", "0.000000"),
    ("KUB", "SHIFT_DOWN_10", "280", "-0.000755", "0.000000"),
    ("KUB", "SCALE_085", "280", "-0.000479", "0.000000"),
    ("KUB", "SCALE_115", "280", "-0.001193", "0.000000"),
    ("KVASIR", "SHIFT_LEFT_10", "87", "0.0000149", "0.000000"),
    ("KVASIR", "SHIFT_RIGHT_10", "87", "0.0000421", "0.000000"),
    ("KVASIR", "SHIFT_UP_10", "87", "0.0000411", "0.000000"),
    ("KVASIR", "SHIFT_DOWN_10", "87", "-0.0000825", "0.000000"),
    ("KVASIR", "SCALE_085", "87", "0.000136", "0.000000"),
    ("KVASIR", "SCALE_115", "87", "0.0000702", "0.000000"),
]

KUB_SUBGROUP_ROBUSTNESS_TABLE = [
    ("Bladder_Stone", "GAUSSIAN_NOISE_HIGH", "432", "-0.341097", "-0.237795"),
    ("Bladder_Stone", "GAUSSIAN_NOISE_LOW", "432", "-0.109659", "-0.065111"),
    ("Bladder_Stone", "GAUSSIAN_BLUR_HIGH", "144", "-0.074989", "-0.014455"),
    ("Bladder_Stone", "RESOLUTION_050", "144", "-0.073459", "-0.014098"),
    ("Bladder_Stone", "BRIGHTNESS_NEG", "144", "-0.023522", "3.14e-10"),
    ("Kidney_Stone", "GAUSSIAN_NOISE_HIGH", "336", "-0.420584", "-0.398294"),
    ("Kidney_Stone", "GAUSSIAN_NOISE_LOW", "336", "-0.132424", "-0.064377"),
    ("Kidney_Stone", "GAUSSIAN_BLUR_HIGH", "112", "-0.031344", "-0.009508"),
    ("Kidney_Stone", "RESOLUTION_050", "112", "-0.029612", "-0.011413"),
    ("Kidney_Stone", "BRIGHTNESS_NEG", "112", "-0.012059", "-0.001855"),
    ("Ureteric_Stone", "GAUSSIAN_NOISE_HIGH", "72", "-0.233187", "-0.172234"),
    ("Ureteric_Stone", "GAUSSIAN_NOISE_LOW", "72", "-0.068921", "-0.046640"),
    ("Ureteric_Stone", "GAUSSIAN_BLUR_HIGH", "24", "-0.060336", "-0.013041"),
    ("Ureteric_Stone", "RESOLUTION_050", "24", "-0.055549", "-0.011133"),
    ("Ureteric_Stone", "BRIGHTNESS_NEG", "24", "0.002337", "0.001125"),
]

# ---------------------------------------------------------------------------
# SECTION 29 — claim ledger (supervisor-facing)
# ---------------------------------------------------------------------------
CLAIM_TABLE = [
    ("C-A1", "Preservation on development population (VAL808)",
     "Phase27 VAL808 preservation freeze", "VAL808 (n=808)",
     "Descriptive preservation / non-inferiority",
     "\"The frozen A8/C9 policy preserves macro-domain Dice relative to the canonical "
     "GlobalMedFiLM global reference on VAL808 (macro DeltaDice 0.002210, 95% bootstrap CI "
     "[0.001133, 0.003298]; lower bound > -0.005).\"",
     "\"improved / superior / outperforms\""),
    ("C-A2", "One-shot ROUTER_HOLDOUT non-inferiority",
     "Phase30 primary non-inferiority result", "ROUTER_HOLDOUT (n=875)",
     "One-shot descriptive non-inferiority WITH disclosed protocol deviation",
     "\"On the one-shot ROUTER_HOLDOUT (n=875) the frozen A8/C9 policy was non-inferior to the "
     "global reference (macro DeltaDice 0.001739, 95% CI [0.001117, 0.002405]).\" "
     "(must carry the Phase30 qualifier)",
     "\"confirmatory / no protocol deviations\""),
    ("C-B1", "Ablation / module contribution",
     "Phase28 13-arm ablation table", "ROUTER_DEVELOPMENT (n=4957)",
     "Descriptive ablation contribution",
     "\"In the frozen 13-arm ablation on ROUTER_DEVELOPMENT, the A8/C9 routing+post-safety policy "
     "achieved mean routed true DeltaDice 0.007516 (benefit capture 0.597, harmful-activation share "
     "0.324), while the F1 integrated refiner did not improve the pipeline (mean -0.000433; "
     "negative result).\"",
     "\"optimal / best / SOTA\""),
    ("C-C1", "Three-seed reproducibility",
     "Phase29 three-seed descriptive summary", "ROUTER_DEVELOPMENT + VAL808",
     "Descriptive reproducibility (no pass/fail gate)",
     "\"The frozen policy reproduced across three seeds (42/123/3407) on ROUTER_DEVELOPMENT "
     "(macro DeltaDice 3-seed mean 0.001215) and VAL808 (mean 0.002822), sign-consistent, "
     "descriptive with no pass/fail gate and no best-seed selection.\"",
     "\"statistically confirmed / significant\""),
    ("C-D1", "One-shot ROUTER_HOLDOUT is the final development validation",
     "Phase30 primary non-inferiority result", "ROUTER_HOLDOUT (n=875)",
     "Descriptive one-shot with disclosed deviation",
     "\"The one-shot ROUTER_HOLDOUT evaluation (n=875) is the final development validation "
     "(A8/C9 macro Dice 0.930287 vs global 0.928548).\"",
     "\"confirmatory / validated without caveat\""),
    ("C-E1", "Statistical governance",
     "Phase31 final closure", "multi-population governance",
     "Governance only; no statistical execution",
     "\"No new confirmatory significance procedure is eligible; the statistical evidence is "
     "descriptive (bootstrap CIs only).\"",
     "\"any confirmatory significance / p-value\""),
    ("C-F1", "External / domain-shift eligibility",
     "Phase32 final closure", "EXTERNAL (19 candidates)",
     "Governance only; no external execution",
     "\"No prospective clean external cohort was eligible; external validation was not "
     "performed (0 of 19 candidates).\"",
     "\"generalizes to external domains\""),
    ("C-G1", "Failure-mode description",
     "Phase33 final closure", "ROUTER_HOLDOUT (n=875)",
     "Descriptive failure analysis",
     "\"Descriptive failure analysis on the frozen ROUTER_HOLDOUT tables: LOW_OVERLAP 10.06% of 875; "
     "harmful router activation 12.92% of the 240 EXECUTE rows; missed-benefit 0; empty-prediction 0; "
     "execute-then-reject 1.67%.\"",
     "\"rare / negligible / clinically safe\""),
    ("C-H1", "Computational efficiency",
     "Phase34 efficiency result", "analytical + measured synthetic batch path (RTX 3060 Ti)",
     "Analytical MAC lower bound / hardware-specific runtime",
     "\"Conditional computation: A8/C9 expected analytical MAC lower bound 3.244e10 (ratio 1.028 vs "
     "global-only; saving 2.345e9 MACs vs always-refine); total frozen parameters 4,837,420; weighted "
     "measured latency 16.589 ms on an RTX 3060 Ti.\"",
     "\"end-to-end / real-time / mobile / energy / hardware-independent\""),
    ("C-I1", "Interpretability (descriptive mechanism evidence)",
     "Phase35 interpretability result", "model-mechanism",
     "Descriptive model-mechanism evidence",
     "\"Descriptive model-mechanism evidence: FiLM parameters are task-modulated; router attribution "
     "concentrates on decoder1 feature groups.\"",
     "\"causes / proves / explains why\""),
    ("C-J1", "Image-perturbation robustness",
     "Phase36 robustness result", "VAL808 (n=808); 12,928 image rows",
     "Development-set synthetic perturbation robustness",
     "\"Synthetic image-perturbation robustness on VAL808: 12,928 paired rows across 16 conditions x "
     "4 domains; clean G reproduction bit-identical.\"",
     "\"real-world acquisition shift / clinically robust\""),
    ("C-K1", "Proposal-perturbation robustness",
     "Phase36 robustness result", "VAL808 (n=808); 4,848 proposal rows",
     "Development-set synthetic perturbation robustness",
     "\"Synthetic proposal-perturbation robustness on VAL808: 4,848 paired rows across 6 proposal "
     "conditions.\"",
     "\"proposal-algorithm variation / proposal-independent\""),
    ("C-L1", "KUB reporting-only subgroup observations",
     "Phase36 robustness result", "VAL808 KUB subset (n=280)",
     "Development-set reporting-only metadata",
     "\"KUB subgroup observations (Kidney_Stone/Bladder_Stone/Ureteric_Stone) are REPORTING-ONLY "
     "metadata, never classes/task-IDs/model inputs.\"",
     "\"any use as class / task_id / model input / routing input\""),
    ("C-T1", "Descriptive final TEST performance",
     "Phase39 v1.2 scientific result", "TEST (n=1683)",
     "POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES",
     "\"RA-MedFiLM-BARR was evaluated descriptively on all 1,683 TEST samples; final-system Dice by "
     "domain (ISIC 735 mean 0.88693; BUSI 174 mean 0.85042; KVASIR 216 mean 0.85071; KUB 558 mean "
     "0.73769) and descriptive macro-domain Dice 0.8314368385956257. No post-hoc TEST sample "
     "exclusion.\"",
     "\"primary endpoint / superior / noninferior / preservation confirmation / benefit over "
     "C-gGLOBAL / harm-free / significant improvement / TEST-confirmed\""),
    ("C-T2", "Missing Phase39 comparative endpoint",
     "Phase39 v1.2 protocol-completeness adjudication", "TEST (n=1683)",
     "PRIMARY_ENDPOINT_NOT_PRODUCED__NOT_DERIVABLE_WITHOUT_NEW_TEST_INFERENCE",
     "\"NOT_ESTABLISHED\"",
     "\"any assertion of TEST comparative result\""),
]

# ---------------------------------------------------------------------------
# SECTION 30 — what we cannot claim
# ---------------------------------------------------------------------------
CANNOT_CLAIM = [
    "Superiority of RA-MedFiLM-BARR over the C-gGLOBAL comparator on TEST.",
    "Non-inferiority of RA-MedFiLM-BARR versus C-gGLOBAL on TEST.",
    "TEST-confirmed preservation of global performance.",
    "Harm-free refinement on TEST.",
    "A statistically significant TEST improvement.",
    "A successful primary comparative endpoint on TEST.",
    "A successful per-domain TEST harm gate.",
    "Any confirmatory TEST result.",
    "That the TEST evaluation was an untouched one-shot TEST execution.",
]

# ---------------------------------------------------------------------------
# SECTION 16 — phase timeline
# ---------------------------------------------------------------------------
PHASE_TIMELINE = [
    ("Phase 27", "Multi-domain preservation evaluation (final system vs global reference)",
     "VAL808 (n=808)", "Macro DeltaDice 0.002210, 95% CI [0.001133, 0.003298]",
     "Descriptive preservation / non-inferiority on the development set",
     "Continuity/development evidence only; NOT a superiority claim"),
    ("Phase 28", "Comprehensive 13-arm module ablation",
     "ROUTER_DEVELOPMENT (n=4957), K=1239",
     "A8/C9 mean routed true DeltaDice 0.007516; F1 refiner negative",
     "Descriptive ablation contribution; no deployment winner selected",
     "Ablation on ROUTER_DEVELOPMENT only; ROUTER_HOLDOUT/TEST/VAL808 reads = 0"),
    ("Phase 29", "Three-seed reproducibility (42/123/3407)",
     "ROUTER_DEVELOPMENT + VAL808",
     "macro DeltaDice 3-seed means 0.001215 / 0.002822",
     "Descriptive reproducibility; sign-consistent across seeds",
     "NO numeric pass/fail gate; no best-seed selection"),
    ("Phase 30", "One-shot ROUTER_HOLDOUT evaluation",
     "ROUTER_HOLDOUT (n=875)",
     "macro DeltaDice 0.001739, 95% CI [0.001117, 0.002405]",
     "One-shot descriptive non-inferiority",
     PHASE30_QUALIFIER),
    ("Phase 31", "Statistical / governance closure",
     "multi-population registry",
     "0 new p-values, 0 new effect sizes, 0 new bootstrap computations",
     "Governance only; statistical evidence is descriptive",
     "NO_NEW_CONFIRMATORY_SIGNIFICANCE_PROCEDURE_IS_ELIGIBLE"),
    ("Phase 32", "External / domain-shift eligibility closure",
     "EXTERNAL (19 candidates)",
     "0 primary-eligible / 0 secondary-eligible / 11 ineligible",
     "Governance only; no external validation performed",
     "NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_ELIGIBLE"),
    ("Phase 33", "Descriptive failure analysis",
     "ROUTER_HOLDOUT (n=875)",
     "LOW_OVERLAP 10.06%; harmful activation 12.92% of EXECUTE; EXECUTE_THEN_REJECT 1.67%",
     "Descriptive failure analysis",
     PHASE30_QUALIFIER),
    ("Phase 34", "Efficiency / resource profile",
     "analytical + measured synthetic batch path",
     "MAC lower bound 3.244e10; weighted latency 16.589 ms",
     "Descriptive analytical compute + hardware-specific runtime",
     "NOT_END_TO_END_PIPELINE_LATENCY; hardware = RTX 3060 Ti"),
    ("Phase 35", "Interpretability / mechanism evidence",
     "model-mechanism",
     "FiLM task-modulated; router attribution concentrated on decoder1",
     "Descriptive model-mechanism evidence",
     "No causal claims"),
    ("Phase 36", "Synthetic robustness studies",
     "VAL808 (n=808)",
     "12,928 image rows; 4,848 proposal rows",
     "Development-set synthetic perturbation robustness",
     "Synthetic perturbations only; not real-world acquisition shift"),
    ("Phase 37-38", "Evidence consolidation and protocol freeze",
     "frozen artifacts (28 + 37 artifacts)",
     "Consolidated evidence tables; frozen protocol manifests",
     "Governance / provenance freeze", NOT_REPORTED),
    ("Phase 39", "Final TEST evaluation",
     "TEST (n=1683)",
     "Descriptive final-system Dice; macro 0.8314368385956257",
     "POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES",
     "Primary comparative endpoint NOT PRODUCED"),
    ("Phase 40", "Manuscript assembly (reduced scope)",
     "manuscript artifacts (17 artifacts)",
     "Frozen manuscript release",
     "MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY",
     "scientific_delta = 0"),
]

# ---------------------------------------------------------------------------
# SECTION 27 — Phase39 protocol history
# ---------------------------------------------------------------------------
PHASE39_HISTORY = [
    ("v1.0 (consumed)",
     "Pre-inference MODEL_LOAD failure (D98: NameError: name 'FEATURE_DIM' is not defined in the "
     "extracted S_omega class closure). test_inference_started=false.",
     "No TEST scientific outcome observed.",
     "Failure artifact SHA-256 19e8d3f5...; process-exit 3924c407...; journal 65c05113..."),
    ("v1.1 (consumed)",
     "Pre-inference preflight failure at stage SCIENCE_LOOP (D99: PHASE39_UNEXPECTED_TASK_DOMAIN: /3; "
     "the manifest domain was read from a non-canonical `domain` field instead of the canonical "
     "`dataset` column).",
     "TEST membership accessed; no TEST image/GT/model-forward/metric result before failure.",
     "Failure artifact SHA-256 e0a1ebe3...; process-exit 4c616957...; journal 3690d1b7...; "
     "START 77486cdf..."),
    ("Post-protocol technical-recovery amendment",
     "A disclosed post-protocol amendment (not a retroactive reinterpretation of the frozen Phase38 "
     "retry policy) repaired D98 and D99 and bound the v1.0+v1.1 history.",
     "Repairs are technical only; no scientific protocol change.",
     "Bound to the v1.0+v1.1 history"),
    ("v1.2 (successful, descriptive)",
     "Evaluated the frozen system on all 1,683 TEST samples.",
     "Descriptive final-system segmentation performance obtained.",
     "Result artifact SHA-256 b9d5c74a316839cace0d085f3a8330f0378755687c6e0b67635371280896959d; "
     "process-exit 717c065f... (exit code 0); journal 5803fcc8...; START 46f109ae..."),
]

# ---------------------------------------------------------------------------
# REFERENCES (30, verbatim from final_reference_audit.json)
# ---------------------------------------------------------------------------
REFERENCES = [
    ("russell1991metareasoning", "Russell, S.; Wefald, E. (1991)",
     "Principles of Metareasoning", "Artificial Intelligence 49(1-3)",
     "10.1016/0004-3702(91)90015-C"),
    ("hor2024adaptiveinference", "Hor, S.; Qian, Y.; Pilanci, M.; Arbabian, A. (2024)",
     "Adaptive Inference: Theoretical Limits and Unexplored Opportunities",
     "arXiv preprint (cs.LG)", "10.48550/arXiv.2402.04359"),
    ("graves2016act", "Graves, A. (2016)",
     "Adaptive Computation Time for Recurrent Neural Networks",
     "arXiv preprint", "10.48550/arXiv.1603.08983"),
    ("viola2001cascade", "Viola, P.; Jones, M. (2001)",
     "Rapid Object Detection Using a Boosted Cascade of Simple Features",
     "CVPR 2001", "10.1109/CVPR.2001.990517"),
    ("latotzke2021cascade", "Latotzke, C.; Loh, J.; Gemmeke, T. (2021)",
     "Cascaded Classifier for Pareto-Optimal Accuracy-Cost Trade-Off Using off-the-Shelf ANNs",
     "LOD 2021 (Springer LNCS)", "10.1007/978-3-030-95470-3_32"),
    ("ren2015fasterrcnn", "Ren, S.; He, K.; Girshick, R.; Sun, J. (2015)",
     "Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks",
     "NeurIPS 2015", "10.48550/arXiv.1506.01497"),
    ("wang2018skipnet", "Wang, X.; Yu, F.; Dou, Z.-Y.; Darrell, T.; Gonzalez, J. E. (2018)",
     "SkipNet: Learning Dynamic Routing in Convolutional Networks",
     "ECCV 2018", "10.48550/arXiv.1711.09485"),
    ("raposo2024mod", "Raposo, D.; Ritter, S.; Richards, B.; Lillicrap, T.; Humphreys, P. C.; Santoro, A. (2024)",
     "Mixture-of-Depths: Dynamically Allocating Compute in Transformer-Based Language Models",
     "arXiv preprint", "10.48550/arXiv.2404.02258"),
    ("jiang2024m4oe", "Jiang, Y.; Shen, Y. (2024)",
     "M4oE: A Foundation Model for Medical Multimodal Image Segmentation with Mixture of Experts",
     "MICCAI 2024 (arXiv:2405.09446)", "10.48550/arXiv.2405.09446"),
    ("kunzel2019metalearners", "Kunzel, S. R.; Sekhon, J. S.; Bickel, P. J.; Yu, B. (2019)",
     "Metalearners for Estimating Heterogeneous Treatment Effects Using Machine Learning",
     "PNAS 116(10)", "10.1073/pnas.1804597116"),
    ("mozannar2020defer", "Mozannar, H.; Sontag, D. (2020)",
     "Consistent Estimators for Learning to Defer to an Expert",
     "ICML 2020", "https://proceedings.mlr.press/v119/mozannar20b.html"),
    ("tian2026deferredseg", "Tian, Z.; Sun, Y.; Wang, Y.; Shi, Y.; Yin, Y. (2026)",
     "DeferredSeg: A Multi-Expert Deferral Framework for Medical Image Segmentation",
     "Pattern Recognition (arXiv:2604.12411)", "10.48550/arXiv.2604.12411"),
    ("wang2023segrefiner", "Wang, M.; Ding, H.; Wang, M.; et al. (2023)",
     "SegRefiner: Towards Model-Agnostic Segmentation Refinement with Discrete Diffusion Process",
     "NeurIPS 2023", "10.48550/arXiv.2312.12425"),
    ("isensee2021nnunet", "Isensee, F.; Jaeger, P. F.; Kohl, S. A. A.; Petersen, J.; Maier-Hein, K. H. (2021)",
     "nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation",
     "Nature Methods 18:203-211", "10.1038/s41592-020-01008-z"),
    ("moon2024jfs", "Moon, S.; Liu, Q. (T.); Kong, H.; Khan, M. H. (2024)",
     "Judging from Support-set: A New Way to Utilize Few-Shot Segmentation for Segmentation Refinement Process",
     "ICIP 2025 (arXiv:2407.04519)", "10.48550/arXiv.2407.04519"),
    ("zhao2026lfpc", "Zhao, X.; Tan, Z.; Sheng, D.; Chen, T.; Liu, Y.; Wu, Y.; Gong, T.; Chu, Q.; Yu, N. (2026)",
     "Learning to Focus and Precise Cropping: A Reinforcement Learning Framework with Information Gaps and Grounding Loss for MLLMs",
     "CVPR 2026 (arXiv:2603.27494)", "10.48550/arXiv.2603.27494"),
    ("bouzid2023scaleaware", "(arXiv:2305.19063, scale-aware SR for lesions) (2023)",
     "Scale-aware Super-resolution Network with Dual Affinity learning for lesion segmentation",
     "arXiv preprint", "10.48550/arXiv.2305.19063"),
    ("chou2024tinylessurvey", "Chou, P.-H.; et al. (2024)",
     "From single to universal: tiny lesion detection in medical imaging",
     "Artificial Intelligence Review 57", "10.1007/s10462-024-10762-x"),
    ("shen2022meddanet", "Shen, H.; Zhang, Y.; Wang, W.; Chen, C.; Liu, J.; Song, S.; Li, J. (2022)",
     "Med-DANet: Dynamic Architecture Network for Efficient Medical Volumetric Segmentation",
     "ECCV 2022 (Springer LNCS)", "10.1007/978-3-031-19803-8_30"),
    ("shen2024meddanetv2", "Shen, H.; Zhang, Y.; Wang, W.; Chen, C.; Liu, J.; Song, S.; Li, J. (2024)",
     "Med-DANet V2: A Flexible Dynamic Architecture for Efficient Medical Volumetric Segmentation",
     "WACV 2024, pp. 7871-7881",
     "https://openaccess.thecvf.com/content/WACV2024/html/Shen_Med-DANet_V2_A_Flexible_Dynamic_Architecture_for_Efficient_Medical_Volumetric_WACV_2024_paper.html"),
    ("zhang2024adaptivepatching", "Zhang, E.; Lyngaas, I.; Chen, Q.; Wang, X.; Igarashi, K.; Huo, Z.; Wahib, M.; Munetomo, M. (2024)",
     "Adaptive Patching for High-resolution Image Segmentation with Transformers",
     "arXiv preprint (cs.CV)", "10.48550/arXiv.2404.09707"),
    ("butoi2023universeg", "Butoi, V. I.; Gonzalez Ortiz, J. J.; Ma, T.; Sabuncu, M. R.; Guttag, J.; Dalca, A. V. (2023)",
     "UniverSeg: Universal Medical Image Segmentation",
     "ICCV 2023, pp. 21438-21451", "10.1109/ICCV51070.2023.01960"),
    ("ma2024medsam", "Ma, J.; He, Y.; Li, F.; Han, L.; et al. (2024)",
     "Segment Anything in Medical Images", "Nature Communications 15:654",
     "10.1038/s41467-024-44824-z"),
    ("laves2018qualitypred", "Laves, M.-H.; Ihler, S.; Ortmaier, T. (2018)",
     "Real-time Prediction of Segmentation Quality", "MICCAI 2018",
     "10.1007/978-3-030-00937-3_18"),
    ("borges2024sdc", "Borges, B. L. C.; Pacheco, B. M.; Silva, D. (2024)",
     "Soft Dice Confidence: A Near-Optimal Confidence Estimator for Selective Prediction in Semantic Segmentation",
     "Machine Learning (2026) / arXiv:2402.10665", "10.1007/s10994-026-07096-w"),
    ("huang2024evanyseg", "Huang, S.; et al. (EvanySeg) (2024)",
     "Towards Ground-truth-free Evaluation of Any Segmentation in Medical Images",
     "arXiv preprint (eess.IV)", "10.48550/arXiv.2409.14874"),
    ("sanisoglu2026abstain", "Sanisoglu, N.; Navab, N.; Kim, S. T. (2026)",
     "Learning to Abstain: Reliable Medical Image Segmentation With Rejection Option",
     "IEEE Access vol. 14, pp. 32655-32665", "10.1109/ACCESS.2026.3669004"),
    ("chow1970reject", "Chow, C. K. (1970)",
     "On Optimum Recognition Error and Reject Tradeoff",
     "IEEE Transactions on Information Theory 16(1)", "10.1109/TIT.1970.1054406"),
    ("tan2026cls", "Tan, B.; et al. (CLS) (2026)",
     "Conformal 3D Lesion Segmentation with Balanced Risk Control",
     "Springer LNCS (MICCAI-adjacent)", "10.1007/978-3-032-38085-2_11"),
    ("zhang2023mobilesam", "Zhang, C.; Han, D.; Qiao, Y.; Kim, J. U.; Bae, S.-H.; Lee, S.; Hong, C. S. (2023)",
     "Faster Segment Anything: Towards Lightweight SAM for Mobile Applications (MobileSAM)",
     "arXiv preprint", "10.48550/arXiv.2306.14289"),
]

# ---------------------------------------------------------------------------
# SECTION 9 — GlobalMedFiLM architecture facts
# ---------------------------------------------------------------------------
GMEDFILM_FACTS = [
    ("Class", "GlobalMedFiLM"),
    ("Architecture ID",
     "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1"),
    ("Parameters", "3,523,001"),
    ("Number of tasks", "4"),
    ("Input", "3 channels, 512 x 512"),
    ("Output", "single-channel global logits [1,H,W] -> p_global = sigmoid(logits)"),
    ("Encoder channels", "encoder1 24 / encoder2 48 / encoder3 96 / encoder4 192 / bridge 256"),
    ("Decoder channels", "decoder4 192 / decoder3 96 / decoder2 48 / decoder1 24"),
    ("FiLM locations", "bridge, decoder4, decoder3, decoder2, decoder1"),
    ("FiLM rule", "F_hat = (1 + gamma) * F + beta ; gamma,beta = tanh(W e + b) ; zero-initialized output"),
    ("Task embedding", "nn.Embedding(4, 32); task conditioning entry point ONLY"),
    ("Output head", "single shared nn.Conv2d(24, 1, kernel_size=1); no dataset-specific head"),
    ("Normalization / activation", "GroupNorm / SiLU"),
    ("BARR feature taps", "bridge (256), decoder1 (24), decoder2 (48)"),
    ("Absent modules", "SE, attention, dropout (G core), deep supervision, per-domain heads"),
]

# Inference semantics (verbatim from methods_final.md section 3.3)
G_INFERENCE_SEMANTICS = [
    "Input tensor shape [3, 512, 512].",
    "fp32 model and fp32 input.",
    "CUDA required for scientific execution.",
    "autocast fp16 enabled.",
    "torch.no_grad() for global inference.",
    "Domain-local contiguous batches of 8.",
    "Canonical probability operator: sigmoid(logits.float()).",
    "Final scoring uses the frozen D75/POLICY_B representation "
    "(live float32, persisted float16, scored float32, threshold >= 0.50).",
]

# ---------------------------------------------------------------------------
# SECTION 10 — ROI extraction
# ---------------------------------------------------------------------------
ROI_FACTS = [
    ("p_global threshold", "0.30", "ROI_PROPOSAL_THRESHOLD"),
    ("Fractional margin", "0.25", "ROI_FRACTIONAL_MARGIN"),
    ("Expansion factor", "x1.5", "(1 + 2*margin) = 1.50; centre-preserving"),
    ("Canvas", "512", "rasterisation canvas"),
    ("Crop", "256", "ROI crop resized to 256 x 256 for R_psi"),
    ("GT involvement", "None", "ROI is GROUND-TRUTH-FREE (derived from p_global only)"),
    ("Empty ROI behaviour", "ACTION_UNAVAILABLE -> FORCED_SKIP", "router and refiner are not invoked"),
]

# ---------------------------------------------------------------------------
# SECTION 11 — B_phi
# ---------------------------------------------------------------------------
BPHI_FACTS = [
    ("Class", "BARRBenefitRouterV1"),
    ("Parameters", "36,801"),
    ("Architecture",
     "nn.Embedding(4,16) + MLP[218 -> 128 -> 64 -> 1] with LayerNorm + SiLU + Dropout(0.10)"),
    ("Numeric input dimension", "202 (192 deep + 10 scalar)"),
    ("Task embedding dimension", "16"),
    ("Total input dimension", "218"),
    ("Output", "1 scalar delta_hat (paired refinement gain); Huber loss delta = 0.05"),
    ("Input scalar normalisation",
     "FIT-only, SCALAR_NORMALIZE_IDX=[192,193,194,195,196,197,200,201], ddof=0"),
    ("Frozen tau (runtime authority)", "tau_C8_final = float -0.024358327623641256 "
     "(exact rational -5003565381643716252018011/205414980000000000000000000)"),
    ("Utility", "U = delta_hat_final - 0.25 * C_ACTION ; C_ACTION = 1051648/10270749"),
    ("Gate", "EXECUTE iff U >= tau_C8_final, else SKIP"),
    ("Bypassed when", "FORCED_SKIP (empty ROI proposal)"),
]

BPHI_FEATURE_GROUPS = [
    ("bridge_global", "bridge", "GLOBAL", "[0, 32)", "32"),
    ("bridge_roi", "bridge", "ROI", "[32, 64)", "32"),
    ("decoder2_global", "decoder2", "GLOBAL", "[64, 96)", "32"),
    ("decoder2_roi", "decoder2", "ROI", "[96, 128)", "32"),
    ("decoder1_global", "decoder1", "GLOBAL", "[128, 160)", "32"),
    ("decoder1_roi", "decoder1", "ROI", "[160, 192)", "32"),
]

BPHI_SCALARS = [
    "entropy_proxy_mean", "frac_prob_within_0p05_of_boundary",
    "frac_prob_within_0p02_of_boundary", "mean_boundary_margin",
    "pred_foreground_fraction", "pred_foreground_pixels", "pred_roi_exists",
    "pred_empty", "predicted_roi_area_fraction", "predicted_roi_side",
]

# ---------------------------------------------------------------------------
# SECTION 12 — R_psi
# ---------------------------------------------------------------------------
RPSI_FACTS = [
    ("Class", "BARRRegionalRefinerV1"),
    ("Parameters", "1,276,401"),
    ("Architecture", "narrowed-channel residual U-Net; channels (16,32,64,96,128); GroupNorm + SiLU"),
    ("Input", "[B, 4, 256, 256] = channels [R, G, B, p_global_crop]"),
    ("Output", "[B, 1, 256, 256] single-channel raw logits, no internal sigmoid"),
    ("Executed when", "EXECUTE branch only"),
    ("Bypassed when", "SKIP_GLOBAL and FORCED_SKIP"),
]

# ---------------------------------------------------------------------------
# SECTION 13 — S_omega
# ---------------------------------------------------------------------------
SOMEGA_FACTS = [
    ("Class", "BARRPostSafetyV1"),
    ("Parameters", "1,217"),
    ("Architecture", "MLP Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)"),
    ("Numeric input dimension", "16"),
    ("Task one-hot dimension", "4"),
    ("Total input dimension", "20"),
    ("Output", "1 scalar safety logit; ACCEPT iff sigmoid(logit) >= 0.50"),
    ("Acceptance threshold", "0.50"),
    ("Normalisation", "None inside S_omega"),
    ("Executed when", "EXECUTE branch only, after R_psi"),
    ("Bypassed when", "SKIP_GLOBAL and FORCED_SKIP"),
]

SOMEGA_NUMERIC_FEATURES = [
    "global_prob_mean", "refined_prob_mean", "mean_abs_prob_change",
    "max_abs_prob_change", "frac_abs_prob_change_ge_0p10", "global_entropy_mean",
    "refined_entropy_mean", "global_foreground_fraction", "refined_foreground_fraction",
    "binary_xor_fraction", "global_component_count", "refined_component_count",
    "global_boundary_fraction", "refined_boundary_fraction",
    "predicted_roi_area_fraction", "predicted_roi_side_normalized",
]

# ---------------------------------------------------------------------------
# SECTION 7 — methodology flow (step-by-step narrative)
# ---------------------------------------------------------------------------
METHOD_FLOW_STEPS = [
    ("Step 1 - Multi-domain input",
     "A [3, 512, 512] image from one of four domains (ISIC, BUSI, KVASIR, KUB) is passed to the "
     "shared global segmenter. Domain identity enters ONLY as a frozen task ID "
     "(0=ISIC, 1=BUSI, 2=KVASIR, 3=KUB)."),
    ("Step 2 - Global prediction (G)",
     "GlobalMedFiLM (3,523,001 parameters) produces global logits; the canonical probability is "
     "p_global = sigmoid(logits.float()). FiLM conditioning modulates five internal stages "
     "(bridge, decoder4/3/2/1) using a learned 32-D task embedding."),
    ("Step 3 - GT-free ROI proposal",
     "A region of interest is derived from p_global alone (threshold 0.30, fractional margin 0.25, "
     "x1.5 expansion; 512 canvas, 256 crop). No ground truth is used. An empty proposal yields "
     "ACTION_UNAVAILABLE and the FORCED_SKIP state."),
    ("Step 4 - 202-D feature assembly",
     "Six groups of 32-D G feature taps (bridge, decoder2, decoder1; each in GLOBAL and ROI scope) "
     "plus 10 prediction/geometry scalars form a ground-truth-free 202-D vector."),
    ("Step 5 - Benefit routing (B_phi)",
     "BARRBenefitRouterV1 (36,801 parameters) consumes the 202-D vector plus a 16-D task embedding "
     "and regresses the paired refinement Dice gain delta_hat. The resource-aware utility "
     "U = delta_hat - 0.25*C is compared with the frozen tau to decide SKIP or EXECUTE."),
    ("Step 6 - Conditional regional refinement (R_psi)",
     "Only on EXECUTE: the ROI crop (RGB plus the global-probability channel, [B,4,256,256]) is "
     "refined by BARRRegionalRefinerV1 (1,276,401 parameters) into a regional probability."),
    ("Step 7 - Post-refinement safety (S_omega)",
     "A 16-D numeric description of the change plus a 4-D task one-hot is scored by "
     "BARRPostSafetyV1 (1,217 parameters); the refinement is ACCEPTED iff sigmoid(logit) >= 0.50."),
    ("Step 8 - Pad-aware fusion and final scoring",
     "Accepted refinements are pasted back into the full-field global probability by the canonical "
     "D61 pad-aware fuse_full_field. Output is scored under the frozen D75/POLICY_B representation "
     "(live f32 -> f16 -> f32, threshold >= 0.50). The pipeline emits exactly one of four states."),
]

# ---------------------------------------------------------------------------
# Appendix B - major phase timeline is PHASE_TIMELINE above
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Supervisor Quick Review
# ---------------------------------------------------------------------------
QUICK_REVIEW = [
    ("What is RA-MedFiLM-BARR?",
     "RA-MedFiLM-BARR (system A8/C9) is a frozen four-component conditional-regional-refinement "
     "pipeline for multi-domain binary medical image segmentation. A shared FiLM-conditioned global "
     "segmenter (GlobalMedFiLM, G) is coupled with a learned benefit router (BARRBenefitRouterV1, "
     "B_phi), an on-demand regional refiner (BARRRegionalRefinerV1, R_psi), and a post-safety "
     "accept/reject stage (BARRPostSafetyV1, S_omega), assembled by pad-aware fusion and a "
     "four-state decision machine with a preserved-output fallback. Total 4,837,420 parameters."),
    ("What is the central research contribution?",
     "The specification and frozen evaluation of a conditional regional-refinement architecture "
     "that decides, BEFORE running the expensive refinement, whether that refinement is expected to "
     "help, and that protects the global prediction when refinement should not be used."),
    ("What is actually novel?",
     "The novelty is at the SYSTEM-INTEGRATION level, not the individual mechanisms. The specific "
     "integration is: (i) a pre-execution, learned regression of the paired GT-derived Dice gain of "
     "an optional regional refinement used as an execute/skip gate; (ii) a post-safety accept/reject "
     "stage with a preserved-output fallback; (iii) applied to multi-domain medical binary "
     "segmentation under an explicit preservation constraint. The gate concept, paired-gain target "
     "formulation, conditional compute, and multi-domain segmentation are individually established "
     "prior art."),
    ("What are the strongest results?",
     "Development preservation on VAL808 (macro DeltaDice 0.002210, 95% CI [0.001133, 0.003298]); "
     "the 13-arm ablation showing A8/C9 mean routed true DeltaDice 0.007516 with an explicitly "
     "reported F1 negative result; three-seed reproducibility; and the one-shot ROUTER_HOLDOUT "
     "non-inferiority (macro DeltaDice 0.001739, 95% CI [0.001117, 0.002405]) with its mandatory "
     "disclosed protocol-deviation qualifier."),
    ("What is the most important limitation?",
     "The frozen Phase39 TEST primary comparative endpoint against C-gGLOBAL was NOT produced. The "
     "successful v1.2 execution emitted descriptive final-system Dice only, so no TEST superiority, "
     "non-inferiority, preservation, or harm-free conclusion can be asserted."),
    ("What can we safely claim in a paper?",
     "The architecture and system-integration contribution; descriptive development preservation "
     "(VAL808); the ablation contribution including the negative result; descriptive three-seed "
     "reproducibility; the one-shot ROUTER_HOLDOUT non-inferiority WITH the mandatory qualifier; "
     "descriptive failure modes; analytical/hardware-specific efficiency; descriptive mechanism "
     "evidence; synthetic image and proposal robustness; KUB reporting-only subgroup observations; "
     "and descriptive final-system TEST Dice."),
    ("What must we NOT claim?",
     "Any TEST superiority, non-inferiority, preservation confirmation, harm-free refinement, "
     "significant TEST improvement, successful comparative primary endpoint, successful TEST harm "
     "gate, or confirmatory TEST result. The TEST evaluation must never be represented as an "
     "untouched one-shot TEST execution; its correct evidence class is "
     "POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES."),
    ("Is the work manuscript-ready?",
     "The frozen manuscript is assembly-complete under the scope "
     "MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY (scientific_delta = 0), with all numbers "
     "provenance-bound and all claims evidence-bound. It is ready for supervisor review and for "
     "submission as a descriptive / methodological report. It is NOT ready to support a claim of "
     "TEST-confirmed comparative benefit against the global reference; that would require a newly "
     "designed study that actually produces the missing comparative endpoint."),
]

# ---------------------------------------------------------------------------
# Metadata fields requiring human completion (permitted placeholders)
# ---------------------------------------------------------------------------
METADATA_PLACEHOLDERS = [
    ("Author", "[AUTHOR NAME]"),
    ("Supervisor", "[SUPERVISOR NAME]"),
    ("Department", "[DEPARTMENT]"),
    ("Institution", "[INSTITUTION]"),
    ("Date", "[DATE]"),
]
