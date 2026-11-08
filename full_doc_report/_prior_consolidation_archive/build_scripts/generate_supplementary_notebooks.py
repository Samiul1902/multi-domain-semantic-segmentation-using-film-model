import nbformat as nbf
import os

# 1. 01_remedfilm_training_history_analysis.ipynb
nb1 = nbf.v4.new_notebook()
nb1.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb1.cells = [
    nbf.v4.new_markdown_cell('# Supplementary Analysis Notebook 01: ReMedFiLM Training History and Convergence Analysis\n\n**Proposed Architecture:** ReMedFiLM (FULL RA-MedFiLM-BARR = $G + B_\\phi + R_\\psi + S_\\omega$, 4.84M params)\n**Internal Backbone:** GlobalMedFiLM ($G$, 3.52M params)\n**Execution Mode:** Strictly Read-Only Scientific Analysis (`ANALYSIS_ONLY = True`). No retraining.'),
    nbf.v4.new_code_cell('''ANALYSIS_ONLY = True
import os, sys, pandas as pd, numpy as np, matplotlib.pyplot as plt

print("Analysis Guard Status: ANALYSIS_ONLY =", ANALYSIS_ONLY)
assert ANALYSIS_ONLY, "Retraining is strictly forbidden!"

df_hist = pd.read_csv('../tables/REMEDFILM_EPOCH_HISTORY.csv')
print(f"Loaded epoch history with {len(df_hist)} epochs.")
df_hist[['epoch', 'train_loss', 'val_loss', 'macro_domain_dice', 'remedfilm_effective_val_dice', 'learning_rate']].head(10)
'''),
    nbf.v4.new_code_cell('''# Convergence Statistics
best_epoch = df_hist.loc[df_hist['remedfilm_effective_val_dice'].idxmax()]
print("Optimal Checkpoint Metric Summary:")
print(f"Best Epoch: {int(best_epoch['epoch'])}")
print(f"Backbone Macro Val Dice (G): {best_epoch['macro_domain_dice']:.4f}")
print(f"ReMedFiLM Full System Val Dice: {best_epoch['remedfilm_effective_val_dice']:.4f}")
print(f"Learning Rate at Peak: {best_epoch['learning_rate']:.2e}")
''')
]
with open('full_doc_report/notebooks_generated/01_remedfilm_training_history_analysis.ipynb', 'w') as f:
    nbf.write(nb1, f)

# 2. 02_remedfilm_ablation_and_routing_analysis.ipynb
nb2 = nbf.v4.new_notebook()
nb2.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb2.cells = [
    nbf.v4.new_markdown_cell('# Supplementary Analysis Notebook 02: ReMedFiLM Ablation and Dynamic Routing Analysis\n\n**Component Decomposition:**\n- Full ReMedFiLM ($G + B_\\phi + R_\\psi + S_\\omega$)\n- Backbone GlobalMedFiLM ($G$)\n- Routing Efficacy of Benefit-Aware Router ($B_\\phi$)\n- Boundary Recovery by Regional Refiner ($R_\\psi$)\n- Degradation Prevention by Safety Gate ($S_\\omega$)\n\n**Execution Mode:** Strictly Read-Only Scientific Analysis (`ANALYSIS_ONLY = True`).'),
    nbf.v4.new_code_cell('''ANALYSIS_ONLY = True
import os, sys, pandas as pd, numpy as np, matplotlib.pyplot as plt

assert ANALYSIS_ONLY, "Retraining is strictly forbidden!"
df_ablation = pd.read_csv('../ReMedFiLM_Ablation_Statistics.csv')
print("Ablation Study Matrix:")
df_ablation
'''),
    nbf.v4.new_code_cell('''# Routing Decision Distribution
df_routing = pd.read_csv('../ReMedFiLM_External_Routing_Safety_Matrix.csv')
print("External Routing and Safety Audit Summary:")
df_routing
''')
]
with open('full_doc_report/notebooks_generated/02_remedfilm_ablation_and_routing_analysis.ipynb', 'w') as f:
    nbf.write(nb2, f)

# 3. 03_remedfilm_external_stress_evaluation.ipynb
nb3 = nbf.v4.new_notebook()
nb3.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb3.cells = [
    nbf.v4.new_markdown_cell('# Supplementary Analysis Notebook 03: ReMedFiLM External Stress and Multi-Center Evaluation\n\n**Datasets Evaluated:**\n- External Out-of-Distribution Benchmarks (ISIC-Ext, BUSI-Ext, KVASIR-Ext, KUB-Ext)\n- Multi-Center Noise and Contrast Stress Testing\n- Negative Case Safety and Spurious Boundary Rejection\n\n**Execution Mode:** Strictly Read-Only Scientific Analysis (`ANALYSIS_ONLY = True`).'),
    nbf.v4.new_code_cell('''ANALYSIS_ONLY = True
import os, sys, pandas as pd, numpy as np, matplotlib.pyplot as plt

assert ANALYSIS_ONLY, "Retraining is strictly forbidden!"
df_ext = pd.read_csv('../ReMedFiLM_External_Evaluation_Matrix.csv')
print("External Generalization Performance:")
df_ext
'''),
    nbf.v4.new_code_cell('''df_neg = pd.read_csv('../ReMedFiLM_External_Negative_Cases.csv')
print("Negative Controls and False Positive Rejection:")
df_neg
''')
]
with open('full_doc_report/notebooks_generated/03_remedfilm_external_stress_evaluation.ipynb', 'w') as f:
    nbf.write(nb3, f)

print('Generated all 3 supplementary analysis notebooks in full_doc_report/notebooks_generated/')
