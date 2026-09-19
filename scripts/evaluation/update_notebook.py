import json

def update_notebook():
    nb_path = "notebooks/13_phase14_regional_refiner_diagnostic.ipynb"
    
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    cells = nb.get("cells", [])
    
    # 1. Mark superseded
    for cell in cells:
        src = "".join(cell.get("source", []))
        if "Step 1 PASS" in src and "DIAGNOSTIC_PROPOSAL_BOTTLENECK" in src:
            if "SUPERSEDED" not in src:
                cell["source"] = ["**SUPERSEDED — INVALID STAGE-4D HEATMAP RESOLUTION 512**\n\n"] + cell["source"]
                
    # 2. Remove empty trailing code cell
    while cells and cells[-1].get("cell_type") == "code" and not "".join(cells[-1].get("source", [])).strip():
        cells.pop()
        
    # Check if Part-3D is already there
    has_part3d = any("## Part-3C/3D Final Canonical Corrected Audit" in "".join(c.get("source", [])) for c in cells)
    if not has_part3d:
        new_md_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Part-3C/3D Final Canonical Corrected Audit\n",
                       "Loads the canonical corrected diagnostic audit and tables."]
        }
        
        new_code_cell = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import json\n",
                "import pandas as pd\n",
                "from pathlib import Path\n",
                "PROJECT_ROOT = Path.cwd().resolve()\n",
                "if PROJECT_ROOT.name == 'notebooks': PROJECT_ROOT = PROJECT_ROOT.parent\n",
                "with open(PROJECT_ROOT / 'reports/audits/phase14_part3_diagnostic_evaluation.json', 'r') as f:\n",
                "    audit = json.load(f)\n",
                "df_img = pd.read_csv(PROJECT_ROOT / 'reports/tables/phase14_part3_image_metrics.csv')\n",
                "val_sized = pd.read_csv(PROJECT_ROOT / 'reports/tables/kub_val_samples_sized.csv')\n",
                "df_img = pd.merge(df_img, val_sized[['sample_id', 'view_type']], on='sample_id')\n",
                "ff_samples = df_img[df_img['view_type'] == 'FULL_FIELD']\n",
                "total_proposals = ff_samples['predicted_proposals_512'].sum()\n",
                "mean_proposals = total_proposals / len(ff_samples)\n",
                "print('=== GLOBAL 512 ===')\n",
                "print(f'Tg: {audit[\"frozen_references\"][\"Tg\"]:.6f}, Dg: {audit[\"frozen_references\"][\"Dg\"]:.6f}')\n",
                "print('=== ORACLE 512 ===')\n",
                "print(f'To: {audit[\"official_512_space\"][\"To_512\"]:.6f}, Do: {audit[\"official_512_space\"][\"Do_512\"]:.6f}')\n",
                "print('=== PREDICTED 512 ===')\n",
                "print(f'Tp: {audit[\"official_512_space\"][\"Tp_512\"]:.6f}, Dp: {audit[\"official_512_space\"][\"Dp_512\"]:.6f}')\n",
                "print('=== GATE ===')\n",
                "print(f'G: {audit[\"official_512_space\"][\"G\"]}')\n",
                "print(f'R: {audit[\"official_512_space\"][\"R\"]}')\n",
                "print(f'Step 1: {audit[\"gates\"][\"step1_pass\"]}')\n",
                "print(f'Step 2: {audit[\"gates\"][\"step2_pass\"]}')\n",
                "print(f'Step 3: {audit[\"gates\"][\"step3_pass\"]}')\n",
                "print(f'Final Classification: {audit[\"diagnostic_classification\"]}')\n",
                "print(f'Total Proposals: {total_proposals}')\n",
                "print(f'Mean Proposals: {mean_proposals}')\n",
                "print(f'Checkpoints: Global (4bffcf926227fb11029ead6bcd8e7dd8ed246e0f1678e3efb2ce4297439a3f2d), Stage-4D (ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace), Regional (89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0)')\n"
            ]
        }
        cells.extend([new_md_cell, new_code_cell])
        
    has_demo = any("## Read-Only Trained-Model KUB Stone Segmentation Demonstration" in "".join(c.get("source", [])) for c in cells)
    if not has_demo:
        demo_md = {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Read-Only Trained-Model KUB Stone Segmentation Demonstration\n",
                       "Deterministic inference on a representative KUB stone."]
        }
        
        demo_code = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import torch\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "import matplotlib.patches as patches\n",
                "from PIL import Image\n",
                "from src.models.factory import create_model\n",
                "from src.utils.checkpointing import load_training_checkpoint\n",
                "from src.data.transforms import SegmentationTransform\n",
                "from src.data.regional_dataset import crop_and_preprocess\n",
                "from src.inference.learned_roi import generate_localizer_rois\n",
                "from src.inference.regional_evaluator import restore_regional_probability, aggregate_and_fuse\n\n",
                "device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\n",
                "global_model = create_model('unetpp', in_channels=1, out_channels=1, base_channels=32).to(device)\n",
                "load_training_checkpoint(PROJECT_ROOT/'checkpoints/phase10_kub_unetpp_seed42_512/best.pt', global_model, restore_rng=False, map_location=device)\n",
                "global_model.eval()\n",
                "localizer_model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16, heatmap_resolution=128).to(device)\n",
                "load_training_checkpoint(PROJECT_ROOT/'checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1/best.pt', localizer_model, restore_rng=False, map_location=device)\n",
                "localizer_model.eval()\n",
                "regional_model = create_model('unet', in_channels=1, out_channels=1, base_channels=32).to(device)\n",
                "load_training_checkpoint(PROJECT_ROOT/'checkpoints/phase14_diag_regional_unet_oracletrain_a3_seed42_v1/best.pt', regional_model, restore_rng=False, map_location=device)\n",
                "regional_model.eval()\n\n",
                "# Select lexicographically first FULL_FIELD VAL sample with >=1 GT component\n",
                "ff_samples = df_img[(df_img['view_type'] == 'FULL_FIELD') & (df_img['has_any_gt'])].sort_values('sample_id')\n",
                "sid = ff_samples.iloc[0]['sample_id']\n",
                "gt_comp_count = ff_samples.iloc[0]['num_gt_components']\n",
                "print(f'Sample ID: {sid}, Split: VAL, FOV: FULL_FIELD, GT Components: {gt_comp_count}')\n",
                "raw_img = Image.open(PROJECT_ROOT / f'data/raw/images/{sid}.png').convert('L')\n",
                "raw_mask_pil = Image.open(PROJECT_ROOT / f'data/raw/masks/{sid}.png').convert('L')\n",
                "raw_mask = (np.asarray(raw_mask_pil)>0).astype(np.uint8)\n",
                "t_orig = SegmentationTransform(512, augment=False)\n",
                "tensor_g, _, meta_g = t_orig(raw_img, raw_mask_pil)\n",
                "with torch.inference_mode():\n",
                "    with torch.amp.autocast(device_type=device.type, enabled=device.type=='cuda'):\n",
                "        logits_g = global_model(tensor_g.unsqueeze(0).to(device))\n",
                "        prob512_g = torch.sigmoid(logits_g)[0,0].cpu().numpy()\n",
                "        logits_l = localizer_model(tensor_g.unsqueeze(0).to(device))\n",
                "        prob128_l = torch.sigmoid(logits_l)[0,0].cpu().numpy()\n",
                "    proposals = generate_localizer_rois(prob128_l, meta_g, (raw_img.height, raw_img.width), 0.10, 0.20, 5, 0.30)\n",
                "    r_probs, r_supp = [], []\n",
                "    for p in proposals:\n",
                "        geom = p['crop_geometry']\n",
                "        c_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, 256)\n",
                "        c_t = torch.from_numpy(np.asarray(c_pil, dtype=np.float32)).unsqueeze(0)/255.0\n",
                "        with torch.amp.autocast(device_type=device.type, enabled=device.type=='cuda'):\n",
                "            logits_r = regional_model(c_t.unsqueeze(0).to(device))\n",
                "        p_r = torch.sigmoid(logits_r)[0,0].cpu().numpy()\n",
                "        rp, rs = restore_regional_probability(p_r, geom, (raw_img.height, raw_img.width))\n",
                "        r_probs.append(rp)\n",
                "        r_supp.append(rs)\n",
                "    def map_global_to_original(p512, meta, osh):\n",
                "        from PIL import ImageOps\n",
                "        l, t, r, b = meta.padding\n",
                "        rw, rh = 512 - l - r, 512 - t - b\n",
                "        p_pil = Image.fromarray(p512).crop((l, t, 512-r, 512-b))\n",
                "        p_pil = p_pil.resize((osh[1], osh[0]), Image.Resampling.BILINEAR)\n",
                "        return np.asarray(p_pil)\n",
                "    prob_orig_g = map_global_to_original(prob512_g, meta_g, (raw_img.height, raw_img.width))\n",
                "    mask_orig_g = (prob_orig_g >= 0.50).astype(np.uint8)\n",
                "    prob_prd = aggregate_and_fuse(prob_orig_g, r_probs, r_supp)\n",
                "    mask_prd = (prob_prd >= 0.50).astype(np.uint8)\n",
                "fig, axes = plt.subplots(2, 3, figsize=(15, 10))\n",
                "axes[0,0].imshow(raw_img, cmap='gray'); axes[0,0].set_title('Input KUB radiograph')\n",
                "axes[0,1].imshow(raw_img, cmap='gray'); axes[0,1].contour(raw_mask, colors='lime'); axes[0,1].set_title('Ground Truth Stone')\n",
                "axes[0,2].imshow(raw_img, cmap='gray'); axes[0,2].contour(mask_orig_g, colors='red'); axes[0,2].set_title('Global UNet++ Prediction')\n",
                "axes[1,0].imshow(raw_img, cmap='gray')\n",
                "for p in proposals:\n",
                "    y1, x1, y2, x2 = p['crop_geometry']\n",
                "    axes[1,0].add_patch(patches.Rectangle((x1,y1), x2-x1, y2-y1, fill=False, edgecolor='blue', lw=2))\n",
                "axes[1,0].set_title('Frozen Stage-4D Proposals')\n",
                "axes[1,1].imshow(raw_img, cmap='gray'); axes[1,1].contour(mask_prd, colors='orange'); axes[1,1].set_title('Regional-Refined Prediction')\n",
                "axes[1,2].imshow(raw_img, cmap='gray'); axes[1,2].contour(raw_mask, colors='lime'); axes[1,2].contour(mask_prd, colors='orange'); axes[1,2].set_title('Prediction Overlay')\n",
                "for ax in axes.flat: ax.axis('off')\n",
                "plt.tight_layout()\n",
                "plt.show()\n",
                "from src.metrics.segmentation import dice_binary\n",
                "from src.metrics.object_metrics import object_metrics\n",
                "print('READ-ONLY DEMONSTRATION — NOT A SEPARATE EXPERIMENT')\n",
                "print(f'Proposal count: {len(proposals)}')\n",
                "print(f'Global Dice: {dice_binary(mask_orig_g, raw_mask):.4f}')\n",
                "print(f'Predicted-regional Dice: {dice_binary(mask_prd, raw_mask):.4f}')\n",
                "print(f'Global FP components: {object_metrics(mask_orig_g, raw_mask, 1)[\"false_positive_predicted_components\"]}')\n",
                "print(f'Predicted FP components: {object_metrics(mask_prd, raw_mask, 1)[\"false_positive_predicted_components\"]}')\n"
            ]
        }
        cells.extend([demo_md, demo_code])
        
    # Make sure we use PROJECT_ROOT instead of Path("reports/...")
    for cell in cells:
        src = "".join(cell.get("source", []))
        if "F = Path('reports/figures" in src:
            cell["source"] = [
                "from IPython.display import Image, display\n",
                "from pathlib import Path\n",
                "PROJECT_ROOT = Path.cwd().resolve()\n",
                "if PROJECT_ROOT.name == 'notebooks': PROJECT_ROOT = PROJECT_ROOT.parent\n",
                "F = PROJECT_ROOT / 'reports/figures/phase14_part3c'\n",
                "Q = PROJECT_ROOT / 'reports/qualitative/phase14_part3c'\n",
                "display(Image(filename=str(F/'figure_A_overall_dice.png'), width=800))\n",
                "display(Image(filename=str(F/'figure_B_recall_stratum.png'), width=800))\n",
                "display(Image(filename=str(F/'figure_C_false_positives.png'), width=800))\n",
                "display(Image(filename=str(F/'figure_D_empty_images.png'), width=800))\n",
                "display(Image(filename=str(F/'figure_E_proposal_burden.png'), width=800))\n",
                "display(Image(filename=str(F/'figure_F_runtime_stacked.png'), width=800))\n",
                "display(Image(filename=str(F/'figure_G_gate_scatter.png'), width=800))\n",
                "display(Image(filename=str(Q/'phase14_part3_qualitative_panel.png'), width=800))\n"
            ]
            
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
        
    print("Notebook updated.")

if __name__ == "__main__":
    update_notebook()
