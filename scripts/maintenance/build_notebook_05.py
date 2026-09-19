import nbformat as nbf

path = r"D:\Softfors\jup\notebooks\05_kub_object_size_taxonomy.ipynb"
nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = {"display_name":"Python 3","language":"python","name":"python3"}
nb.cells = [
    nbf.v4.new_markdown_cell(
        "# FOV-Aware KUB Object-Size Taxonomy\n"
        "This live report runs the reconciled Phase 7-R1 pipeline from frozen `phase4_v2` manifests. "
        "Thresholds use TRAIN FULL_FIELD components only; TEST masks and external data are not accessed."
    ),
    nbf.v4.new_code_cell(
        "import sys, pandas as pd\n"
        "from pathlib import Path\n"
        "from IPython.display import Image, display\n"
        "ROOT = Path(r'D:\\Softfors\\jup')\n"
        "if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))\n"
        "from src.utils.manifest_guard import verify_manifests\n"
        "from src.analysis.kub_object_size import load_phase7_artifacts, validate_phase7_artifacts\n"
        "T=ROOT/'reports'/'tables'; A=ROOT/'reports'/'audits'\n"
        "verify_manifests()\n"
        "artifacts=load_phase7_artifacts(ROOT)\n"
        "assert validate_phase7_artifacts(artifacts)\n"
        "ss=artifacts['fov_samples']; cs=artifacts['fov_components']\n"
        "sc=artifacts['fov_sample_category']; cc=artifacts['fov_component_category']\n"
        "sz=artifacts['category_size']; tv=artifacts['train_val_size']\n"
        "print('Manifest guard and source-of-truth assertions: PASS')\n"
        "print('TEST mask reads:', int(artifacts['provenance']['test_mask_reads']))"
    ),
    nbf.v4.new_markdown_cell("## Reconciled sample-level and component-level FOV tables"),
    nbf.v4.new_code_cell(
        "display(ss); display(sc); display(cs); display(cc)\n"
        "display(pd.read_csv(T/'kub_fov_characteristics_v2.csv'))\n"
        "display(pd.read_csv(T/'kub_fov_patient_summary_v2.csv'))"
    ),
    nbf.v4.new_markdown_cell("## Frozen taxonomy, subgroup counts, patients, and validation transfer"),
    nbf.v4.new_code_cell(
        "display(artifacts['thresholds'])\n"
        "display(sz); display(tv)\n"
        "display(artifacts['patients_per_stratum'])\n"
        "display(artifacts['patient_summary'])\n"
        "mc=artifacts['multicomponent']\n"
        "multi_n=len(mc); mixed_n=int(mc.mixed_strata.sum()); tiny_larger=int(mc.tiny_plus_larger.sum())\n"
        "display(pd.DataFrame({'metric':['FULL_FIELD images','Multi-component images','Multi-component % of FULL_FIELD','Mixed-stratum images','Mixed % among multi-component','Mixed % among all FULL_FIELD','TINY + larger'],'value':[771,multi_n,100*multi_n/771,mixed_n,100*mixed_n/multi_n,100*mixed_n/771,tiny_larger]}))"
    ),
    nbf.v4.new_markdown_cell("## Publication figures"),
    nbf.v4.new_code_cell(
        "F=ROOT/'reports'/'figures'/'kub_object_size'\n"
        "stems=['kub_fov_composition_v2','kub_fov_dimension_distribution_v2',"
        "'kub_fullfield_object_size_thresholds_v2','kub_object_size_by_category_v2',"
        "'kub_object_size_train_val_v2','kub_roi_vs_fullfield_object_ratio_v2',"
        "'kub_multicomponent_size_combinations_v2']\n"
        "for stem in stems:\n    print(stem); display(Image(filename=str(F/f'{stem}.png')))"
    ),
    nbf.v4.new_markdown_cell("## Deterministic qualitative panels"),
    nbf.v4.new_code_cell(
        "Q=ROOT/'reports'/'qualitative'/'kub_size_taxonomy'\n"
        "display(Image(filename=str(Q/'kub_size_strata_examples_v2.png')))\n"
        "display(Image(filename=str(Q/'kub_roi_examples_v2.png')))"
    ),
    nbf.v4.new_markdown_cell(
        "## Measured interpretation and limitations\n"
        "TRAIN has 771 FULL_FIELD samples (1,162 components) and 1,208 ROI_CROP samples "
        "(1,214 components); sample and component units are reported separately. "
        "Among 771 FULL_FIELD training images, 206 (26.72%) contained multiple connected components. "
        "Of these 206 images, 135 (65.53%) contained components spanning more than one dataset-relative "
        "size stratum; those 135 images are 17.51% of all FULL_FIELD images. Forty-four contained a TINY "
        "component plus a larger component. Component-level exposure shows 183 patients represented one "
        "stratum, 100 represented two, 30 represented three, and 3 represented all four; therefore 133 "
        "of 316 FULL_FIELD patients represented at least two strata. The earlier value 69 used variation "
        "in image-level dominant strata and did not implement the component-exposure definition. "
        "`kub_size_v1` remains unchanged and is estimated from TRAIN FULL_FIELD components only. "
        "All strata are dataset-relative, not clinical/mm grades. VAL uses frozen TRAIN thresholds. "
        "TEST morphology and external data remain unaccessed."
    ),
]
nb.metadata.phase = "7-R2"
nb.metadata.taxonomy_version = "kub_size_v1"
nbf.write(nb, path)
print(path)
