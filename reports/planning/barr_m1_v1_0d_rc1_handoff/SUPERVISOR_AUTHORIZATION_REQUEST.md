# Request for independent supervisor decision ? BARR-M1 RC1

**Request only. NOT APPROVED. No signature or approving identity supplied.**

Responsible supervisor/delegated authority: **to be supplied by the real authority**.
Authorization ID, institutional role/delegation evidence, approval date and expiry:
**to be supplied through the institution's established channel**.

Requested scope:

- Study BARR-M1; DESCRIPTIVE_POLICY_COMPARISON; claims DESCRIPTIVE_DEV only.
- Arms A0, A1, A8 only; ROUTER_DEVELOPMENT n=4957; IN_SAMPLE.
- Mode CPU_ONLY_RE_ANALYSIS_ONLY; frozen arrays and already frozen decisions only.
- Paired equal-domain macro Dice contrasts A8-A0, A8-A1, A1-A0.
- Domain-stratified paired bootstrap: 2000 resamples, seed 42; KUB patient clusters
  (267); ISIC/BUSI/KVASIR per-case because patient grouping is NOT_AVAILABLE.
- Harm: delta < 0 and delta < -1e-9; all-population and applied-case conditional
  rates separately. Pooled measures never replace equal-domain macro measures.
- A8 budget 0.25; 1239 selected candidates, 1205 accepted, 34 rejected.
- No TEST, ROUTER_HOLDOUT, external evaluation/inference, training, optimizer steps,
  model construction/forward inference, A7 analysis, BARR-M2, FiLM-off control,
  EXT-03B training, EXT-04 onward, or new retrospective arms.
- No component-isolation, isolated-router causality, clinical-safety, superiority
  or independent-generalization claims.

Executable: `scripts/analysis/barr_m1_release_candidate_v1_0d_rc1.py`

**Approved executable SHA to bind:** `1021c9b2b73227b6401d46000f7d108bd8e577cbcf6901f61d88f23fab4b1af8`

Original frozen protocol/request SHA: `a1a59cffc83e7b167b6ae28f75123167abf06d37d080e09c3cc0cdf519419a42`.
Separate existing erratum SHA: `7653cefd5b1bf6a1e28e5c9f65e1850a561f7316d48226dfb0859195c1c38f45`.
Both are mandatory reading and both digests are signature-bound.
The unchanged frozen v1.0c gate remains `e82ecdb781a56355a9a0a1ebabd948932fee0e15e71d90770bbd0b8459e96c32`.

| Frozen input | Path | SHA-256 |
|---|---|---|
| phase25c_oof_labels | `data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv` | `fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f` |
| phase25e_c8_membership | `reports/tables/phase25e_policy_memberships_v1_0/C8_lambda0.25_budget0.25.csv` | `4c411d589866434b824245d3c940bc09873f3cbc096ddc8a44776cd56273393b` |
| phase25f_oof_safety | `data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv` | `a9f63edd6d58a9a1d78a052a3e4539c6e0dd4d68bfb1c09c4c36789c441ebdee` |
| phase25b_dev_metadata | `data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv` | `ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093` |
| patient_grouping | `manifests/phase4_v3/train.csv` | `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6` |

The first four inputs are bound by the frozen gate. The train-manifest grouping
source was identified in the completed lineage record and its digest recorded
in v1.0d; it is explicitly included for this approval, not retroactively inserted
into the v1.0c manifest. Development identity is the exact Phase-25B metadata SHA
above: BUSI 512, ISIC 2173, KUB 1680, KVASIR 592. Join only by sample_id.
Checkpoint SHAs in [release_identity.json](release_identity.json) are lineage
references only; checkpoints must never be opened by this reanalysis.

## Required signed approval contents

Use the exact payload contract in [TRUST_AND_LAUNCH_CONTRACT.md](TRUST_AND_LAUNCH_CONTRACT.md).
Signature must bind the authorization ID, real named approver, UTC approval/expiry,
exact arms/population/mode/exclusions, protocol plus erratum, complete input and
checkpoint lineage SHA maps, and the executable SHA above. The descriptive claim
boundary is bound through the immutable protocol/erratum and classification.
A plain JSON declaration or approved=true is insufficient.

Separately authenticate the SHA-256 fingerprint of the approver's raw Ed25519
public key through an existing institutional directory or direct authenticated
channel. Record who verified it and the evidence outside this repository.
Do not derive trust from the signed payload itself. Do not send a private key.

**Exact next action:** review these materials and communicate the accountable
supervisor's signed decision. If approving, coordinate independent public-key
provisioning and trustworthy time/revocation service with the machine administrator.
After those are verified, issue a **later, separate explicit launch work order**.
Neither this request nor an approval by itself permits launch.
