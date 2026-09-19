"""Publication figures for Phase-11 source CSVs."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
ROOT=Path(__file__).resolve().parents[2]; T=ROOT/'reports/tables'; F=ROOT/'reports/figures/phase11_kub_failure_analysis'; F.mkdir(parents=True,exist_ok=True); sns.set_theme(style='whitegrid')
def emit(fig,name):
 for ext in ('png','svg','pdf'): fig.savefig(F/f'{name}.{ext}',dpi=320,bbox_inches='tight')
 plt.close(fig)
x=pd.read_csv(T/'phase11_kub_failure_analysis_per_image.csv'); c=pd.read_csv(T/'phase11_kub_failure_analysis_per_component.csv'); s=pd.read_csv(T/'phase11_kub_failure_summary.csv'); o=pd.read_csv(T/'phase11_cross_model_failure_overlap.csv'); fp=pd.read_csv(T/'phase11_fp_unetpp_vs_deeplab.csv'); m=pd.read_csv(T/'phase11_kub_multicomponent_failure.csv')
fig,ax=plt.subplots(figsize=(7,5)); sns.violinplot(x=x.FOV,y=x.dice,inner='quartile',cut=0,ax=ax); ax.set_ylim(0,1); ax.set_title('UNet++ VAL Dice by FOV'); emit(fig,'phase11_dice_by_fov_distribution')
fig,ax=plt.subplots(figsize=(8,5)); sns.scatterplot(x=x.gt_foreground_ratio,y=x.dice,hue=x.FOV,alpha=.75,ax=ax); ax.set_xscale('log'); ax.set_ylim(0,1); ax.set_title('UNet++ Dice versus original GT foreground ratio'); emit(fig,'phase11_dice_vs_foreground_ratio')
fig,ax=plt.subplots(figsize=(9,5)); sns.stripplot(data=c,x='original_component_ratio',y='detected_unetpp',hue='kub_size_v1',jitter=.12,ax=ax); ax.set_xscale('log');
for q in [0.0001499766777599,0.00033976472454305,0.0008266496069636999]: ax.axvline(q,color='black',ls='--',lw=1)
ax.set_title('FULL_FIELD original-component detection versus size'); emit(fig,'phase11_component_detection_vs_size')
fig,ax=plt.subplots(figsize=(11,5)); sns.barplot(s,x='Failure_Type',y='Count',color='#4C72B0',ax=ax); ax.tick_params(axis='x',rotation=55); ax.set_ylim(bottom=0); ax.set_title('Reproducible descriptive failure taxonomy'); emit(fig,'phase11_failure_taxonomy_counts')
fig,ax=plt.subplots(figsize=(7,5)); sns.boxplot(data=x[x.hd95_valid],x='FOV',y='hd95',showfliers=False,ax=ax); ax.set_ylim(bottom=0); ax.set_title('Valid UNet++ HD95 by FOV'); emit(fig,'phase11_hd95_by_fov')
fig,ax=plt.subplots(figsize=(7,6)); sns.scatterplot(data=x,x='recall',y='precision',hue='FOV',style='low_dice_decile',ax=ax); ax.axvline(.5,color='gray',ls='--'); ax.axhline(.5,color='gray',ls='--'); ax.set_xlim(0,1.02); ax.set_ylim(0,1.02); ax.set_title('UNet++ per-image precision–recall failure map'); emit(fig,'phase11_precision_recall_failure_map')
fig,ax=plt.subplots(figsize=(11,5)); sns.barplot(o,x='Failure_Category',y='N_Images',color='#55A868',ax=ax); ax.tick_params(axis='x',rotation=45); ax.set_ylim(bottom=0); ax.set_title('Cross-model failure overlap'); emit(fig,'phase11_cross_model_failure_overlap')
fig,ax=plt.subplots(figsize=(7,6)); sns.scatterplot(fp,x='fp_eval_components',y='fp_deeplabv3plus',hue='FOV',size='dice',ax=ax); lim=max(fp.fp_eval_components.max(),fp.fp_deeplabv3plus.max()); ax.plot([0,lim],[0,lim],ls='--',color='gray'); ax.set_xlim(left=0); ax.set_ylim(bottom=0); ax.set_title('FP burden: UNet++ versus DeepLabV3+'); emit(fig,'phase11_fp_burden_unetpp_vs_deeplab')
fig,axes=plt.subplots(1,2,figsize=(11,4)); sns.countplot(m,x='detection_class',ax=axes[0]); axes[0].tick_params(axis='x',rotation=25); axes[0].set_ylim(bottom=0); sns.histplot(m,x='fraction_detected',bins=10,ax=axes[1]); axes[1].set_xlim(0,1); fig.suptitle('FULL_FIELD multi-component detection failures'); emit(fig,'phase11_multicomponent_failure')
