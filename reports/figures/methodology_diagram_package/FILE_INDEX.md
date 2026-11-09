# FILE INDEX — RA-MedFiLM-BARR Methodology Diagram Evidence Package

> **Start here.** The human supervisor only needs this one folder:
> `D:\Softfors\jup\reports\figures\methodology_diagram_package\`

All hashes are **on-disk byte SHA-256**. Package generated with **zero new model inference**.

---

## 1. Upload these first  ⬅ (give these to the diagram AI)

| # | File | What it is | SHA-256 |
|---|---|---|---|
| 1 | `README.md` | Governance + verified domain/task mapping + figure recommendation | `085dc5fcc94eb1ab79bc1aac4ac164420187cead5591a569aa5b600aa438a73c` |
| 2 | `methodology_diagram_manifest.json` | Master manifest: architecture, BARR components, dims, population, samples | — |
| 3 | `domain_task_mapping.csv` | task_id → domain / modality / target / class count | — |
| 4 | `domain_subclass_mapping.csv` | Authoritative subclass status per domain | — |
| 5 | `architecture_flow.json` | Node-by-node scientific data flow with dims + thresholds | — |
| 6 | `tensor_dimension_contract.json` | All exact dimensions + parameter counts | — |
| 7 | `thresholds_and_decisions.json` | All thresholds + decision/state vocabulary | — |
| 8 | `robustness_protocol.json` | Frozen Phase36 robustness design | — |
| 9 | `four_domain_input_montage.png` | BUSI \| ISIC \| KUB \| KVASIR inputs (labelled) | — |
| 10 | `four_domain_input_gt_montage.png` | Same, with GT boundaries | — |

## 2. Domain images (representative samples, VAL808)

Each folder: `01_input.png`, `02_ground_truth.png`, `03_input_gt_overlay.png`,
`04_global_probability.png`, `05_roi_proposal.png`, `07_final_segmentation.png`,
`sample_metadata.json`.  Panel `06_regional_refinement` is omitted
(`NOT_AVAILABLE_WITHOUT_NEW_MODEL_EXECUTION`).

| Folder | Sample (VAL808) | task_id | category | frozen state |
|---|---|---|---|---|
| `representative_samples/ISIC/` | `193d19a4…` | 0 | NOT_AVAILABLE | EXECUTE_THEN_ACCEPT |
| `representative_samples/BUSI/` | `15389cbf…` | 1 | NOT_AVAILABLE | SKIP_GLOBAL |
| `representative_samples/KVASIR/` | `b6509a88…` | 2 | NOT_AVAILABLE | SKIP_GLOBAL |
| `representative_samples/KUB/` | `80e180bd…` | 3 | Kidney_Stone (reporting only) | EXECUTE_THEN_ACCEPT |

> 04 and 07 coincide for SKIP_GLOBAL samples — that is the frozen behaviour (final = global).

## 3. Optional supporting visuals (`existing_visual_references/`)

| File | Type | Purpose |
|---|---|---|
| `global_medfilm_structure.png` | schematic (NEW, source-derived) | G encoder/bridge/decoder + FiLM sites |
| `pre_refinement_202d_feature_breakdown.png` | schematic (NEW, source-derived) | 202-D composition |
| `post_safety_20d_breakdown.png` | schematic (NEW, source-derived) | 16-D + 4-D = 20-D |
| `p24_full_system_architecture.png` | schematic (existing) | full system design |
| `p24_pre_gate_vs_post_safety.png` | schematic (existing) | gate vs post-safety |
| `p26_canonical_inference_state_machine.png` | schematic (existing) | 4-state inference machine |
| `p26_bundle_component_graph.png` | schematic (existing) | 4-component bundle |
| `p25a_roi030_refiner_architecture_summary.png` | schematic (existing) | R_psi architecture |
| `phase13_predicted_roi_localization_panel.png` | scientific result (existing) | predicted-ROI localization |
| `phase35_f1_film_gamma_heatmap.png` | scientific result (existing) | FiLM gamma analysis |
| `phase35_f6_router_group_attribution.png` | scientific result (existing) | B_phi feature attribution |
| `phase21_detailed_gallery_{ISIC,BUSI,KUB,KVASIR}.png` | scientific result (existing) | per-domain segmentation galleries |

## 4. Source evidence

| File | Purpose |
|---|---|
| `source_provenance.json` | Every claim → source path + SHA + symbol + confidence |
| `_sample_build_summary.json` | Machine summary of sample build (no inference) |
| Build scripts | `scripts/analysis/build_methodology_package_samples.py`, `..._montages.py`, `..._schematics.py` |

---

### Package file SHA-256 (byte)

```
README.md                                             085dc5fcc94eb1ab79bc1aac4ac164420187cead5591a569aa5b600aa438a73c
methodology_diagram_manifest.json                      d4853df40c400d0b9ca7ecdd61227625dbc62ee32a138083aa073767ae5129ec
domain_task_mapping.csv                                654eff4e17cb8643e7fcd02d982936925fb9abc832c74930e0b8ccb9d5a02bfc
domain_subclass_mapping.csv                            55addf12b83f0c5e2ea90553568a2c2ae4a9317f414041075120462410aed399
architecture_flow.json                                 6fb6377d80b3f38ec6b77ac9b34922de7daeb49115d387404122a2bff88c8b3a
tensor_dimension_contract.json                         d5e4d96d44217ba7db5e4f0e0f25b7d595b9d8fb3c4b78871118b2a83ff81cff
thresholds_and_decisions.json                          b9254cdb6dd3d1bba6be1a45373ce37fb66f8b90ceee384c8f29bf5318717d01
robustness_protocol.json                               d3cf2f04d933b64fb02153495adbdd49eb3a4e937c103566d59ce550113f0313
four_domain_input_montage.png                          91ee45ed450cbe22ed5baea9d3e96896b903e246832b66ef752df624d481ada4
four_domain_input_gt_montage.png                       c2fe78accc1ba9a09d9c112a9d2efde4f6cda13759da3ab496b66dc75ea31ea3
source_provenance.json                                 39d7b74254247e703ef665dacfc69d84f7ec9e781e0fc61b437c30d5004265e7
```

> `FILE_INDEX.md` cannot list its own hash without changing it; recompute with
> `certutil -hashfile FILE_INDEX.md SHA256` if a frozen record is required.
