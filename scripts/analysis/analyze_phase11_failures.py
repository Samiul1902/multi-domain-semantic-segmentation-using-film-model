"""Phase 11 deterministic VAL-only failure analysis from finalized tables."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
T=ROOT/'reports/tables'; A=ROOT/'reports/audits'
MODELS={'unet':'phase9_unet','attention_unet':'phase10_attention_unet','unetpp':'phase10_unetpp','deeplabv3plus':'phase10_deeplabv3plus'}

def save(df,name,paper=False):
 p=T/name; df.to_csv(p,index=False)
 if paper:
  h=list(df.columns); lines=['| '+' | '.join(h)+' |','| '+' | '.join(['---']*len(h))+' |']; lines += ['| '+' | '.join(map(str,row))+' |' for row in df.itertuples(index=False,name=None)]; p.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); p.with_suffix('.tex').write_text(df.to_latex(index=False),encoding='utf-8')
 return p

def main():
 primary=pd.read_csv(T/'phase10_unetpp_val_per_image.csv'); comp=pd.read_csv(T/'phase10_unetpp_val_per_component.csv'); meta=pd.read_csv(T/'kub_val_samples_sized.csv')
 meta_cols=['sample_id','foreground_ratio','dominant_object_stratum','contains_tiny_object','contains_small_object','contains_medium_object','contains_large_object']
 x=primary.merge(meta[meta_cols],on='sample_id',validate='one_to_one')
 low=float(x.dice.quantile(.10)); high_hd=float(x.loc[x.hd95_valid,'hd95'].quantile(.90)); high_fp=float(x.false_positive_components.quantile(.90))
 x['low_dice_decile']=x.dice<=low; x['high_hd95_decile']=x.hd95_valid & (x.hd95>=high_hd); x['high_fp_decile']=x.false_positive_components>=high_fp
 missed=comp.loc[(comp.view_type=='FULL_FIELD') & ~comp.detected].groupby(['sample_id','kub_size_v1_stratum']).size().unstack(fill_value=0)
 for size in ['TINY','SMALL','MEDIUM','LARGE']: x[f'missed_{size.lower()}_component']=x.sample_id.map(missed.get(size,pd.Series(dtype=int))).fillna(0).astype(int)>0
 cstats=comp.groupby('sample_id').detected.agg(['sum','count']).rename(columns={'sum':'detected_original','count':'original_components_table'})
 x=x.join(cstats,on='sample_id'); multi=x.view_type.eq('FULL_FIELD') & x.original_component_count.gt(1)
 x['partial_multi_component_detection']=multi & x.detected_original.gt(0) & x.detected_original.lt(x.original_components_table)
 x['complete_multi_component_miss']=multi & x.detected_original.eq(0)
 labels=[('EMPTY_PREDICTION',x.empty_prediction),('LOW_DICE_DECILE',x.low_dice_decile),('HIGH_HD95_DECILE',x.high_hd95_decile),('HIGH_FP_DECILE',x.high_fp_decile),('MISSED_TINY_COMPONENT',x.missed_tiny_component),('MISSED_SMALL_COMPONENT',x.missed_small_component),('PARTIAL_MULTI_COMPONENT_DETECTION',x.partial_multi_component_detection),('COMPLETE_MULTI_COMPONENT_MISS',x.complete_multi_component_miss)]
 x['failure_labels']=[';'.join(name for name,mask in labels if bool(mask.iloc[i])) for i in range(len(x))]
 out=x.rename(columns={'view_type':'FOV','original_component_count':'component_count_original','foreground_ratio':'gt_foreground_ratio','gt_evaluation_component_count':'gt_eval_components','predicted_component_count':'pred_eval_components','detected_gt_components':'detected_eval_components','missed_gt_components':'missed_eval_components','false_positive_components':'fp_eval_components'})
 keep=['sample_id','patient_id','category','FOV','component_count_original','gt_foreground_ratio','dominant_object_stratum','dice','iou','precision','recall','hd95','hd95_valid','empty_prediction','gt_eval_components','pred_eval_components','detected_eval_components','missed_eval_components','fp_eval_components','low_dice_decile','high_hd95_decile','high_fp_decile','failure_labels']
 save(out[keep],'phase11_kub_failure_analysis_per_image.csv')
 # Original-space aligned component detections across all models.
 keys=['sample_id','patient_id','category','view_type','original_component_id','original_component_pixels','original_component_ratio','kub_size_v1_stratum']
 cc=comp[keys].copy()
 for model,stem in MODELS.items():
  z=pd.read_csv(T/f'{stem}_val_per_component.csv'); idcol='component_id' if model=='unet' else 'original_component_id'; z=z.rename(columns={idcol:'original_component_id'})
  cc=cc.merge(z[['sample_id','original_component_id','detected']].rename(columns={'detected':f'detected_{model}'}),on=['sample_id','original_component_id'],validate='one_to_one')
 cc=cc[cc.view_type=='FULL_FIELD'].rename(columns={'view_type':'FOV','original_component_id':'component_id','kub_size_v1_stratum':'kub_size_v1','detected_attention_unet':'detected_attention_unet'})
 dcols=['detected_unet','detected_attention_unet','detected_unetpp','detected_deeplabv3plus']; cc['models_detecting_count']=cc[dcols].sum(axis=1); cc['missed_by_all']=cc.models_detecting_count.eq(0); cc['detected_by_all']=cc.models_detecting_count.eq(4); cc['detected_unetpp_only']=cc.detected_unetpp & cc.models_detecting_count.eq(1); cc['missed_unetpp_detected_other']=~cc.detected_unetpp & cc[dcols].drop(columns='detected_unetpp').any(axis=1)
 save(cc,'phase11_kub_failure_analysis_per_component.csv')
 # Multi-component image distributions, original component space.
 multi_table=x[multi][['sample_id','patient_id','category','original_component_count','dice','detected_original','original_components_table']].copy(); multi_table['missed_original_components']=multi_table.original_components_table-multi_table.detected_original; multi_table['fraction_detected']=multi_table.detected_original/multi_table.original_components_table; multi_table['detection_class']=np.select([multi_table.detected_original.eq(multi_table.original_components_table),multi_table.detected_original.eq(0)],['COMPLETE_DETECTION','COMPLETE_MISS'],default='PARTIAL_DETECTION'); save(multi_table,'phase11_kub_multicomponent_failure.csv')

 # Patient-level summary uses primary-model images and original-space components.
 patient_comp=comp.groupby('patient_id').detected.agg(original_components='count',detected_original_components='sum'); patient=x.groupby('patient_id').agg(N_images=('sample_id','size'),mean_dice=('dice','mean'),median_dice=('dice','median'),worst_dice=('dice','min'),empty_prediction_count=('empty_prediction','sum'),FP_eval_components=('false_positive_components','sum')).join(patient_comp); patient['missed_original_components']=patient.original_components-patient.detected_original_components; patient=patient.reset_index(); save(patient,'phase11_kub_failure_by_patient.csv')
 # Cross-model image failure overlap, with low-performing defined against each model's own descriptive bottom decile.
 image_cross=x[['sample_id','patient_id','category','view_type']].copy(); low_cols=[]
 for model,stem in MODELS.items():
  z=pd.read_csv(T/f'{stem}_val_per_image.csv')[['sample_id','dice','false_positive_components']].rename(columns={'dice':f'dice_{model}','false_positive_components':f'fp_{model}'}); image_cross=image_cross.merge(z,on='sample_id',validate='one_to_one'); cutoff=float(z[f'dice_{model}'].quantile(.10)); image_cross[f'low_{model}']=image_cross[f'dice_{model}']<=cutoff; low_cols.append(f'low_{model}')
 others_unetpp=image_cross[['low_unet','low_attention_unet','low_deeplabv3plus']]; others_deeplab=image_cross[['low_unet','low_attention_unet','low_unetpp']]
 image_cross['failure_category']=np.select([image_cross[low_cols].all(axis=1),~image_cross[low_cols].any(axis=1),~image_cross.low_unetpp & others_unetpp.all(axis=1),~image_cross.low_deeplabv3plus & others_deeplab.all(axis=1),image_cross.low_unetpp & ~others_unetpp.any(axis=1),image_cross.low_deeplabv3plus & ~others_deeplab.any(axis=1)],['ALL_FOUR_LOW','ALL_FOUR_NOT_LOW','UNETPP_UNIQUELY_SUCCESSFUL','DEEPLAB_UNIQUELY_SUCCESSFUL','UNETPP_UNIQUELY_LOW','DEEPLAB_UNIQUELY_LOW'],default='ARCHITECTURE_DISAGREEMENT'); save(image_cross,'phase11_cross_model_failure_per_image.csv')
 overlap=image_cross.failure_category.value_counts().rename_axis('Failure_Category').reset_index(name='N_Images'); component_overlap=pd.DataFrame([{'Failure_Category':'COMPONENT_MISSED_BY_ALL','N_Images':int(cc.missed_by_all.sum())},{'Failure_Category':'COMPONENT_DETECTED_BY_ALL','N_Images':int(cc.detected_by_all.sum())},{'Failure_Category':'COMPONENT_DETECTED_UNETPP_ONLY','N_Images':int(cc.detected_unetpp_only.sum())},{'Failure_Category':'COMPONENT_MISSED_UNETPP_DETECTED_OTHER','N_Images':int(cc.missed_unetpp_detected_other.sum())}]); overlap=pd.concat([overlap,component_overlap],ignore_index=True); save(overlap,'phase11_cross_model_failure_overlap.csv',True)
 # FP comparator and descriptive strata cutoffs.
 dl=pd.read_csv(T/'phase10_deeplabv3plus_val_per_image.csv')[['sample_id','dice','false_positive_components']].rename(columns={'dice':'dice_deeplabv3plus','false_positive_components':'fp_deeplabv3plus'}); fpcompare=out[['sample_id','category','FOV','dominant_object_stratum','dice','fp_eval_components']].merge(dl,on='sample_id'); save(fpcompare,'phase11_fp_unetpp_vs_deeplab.csv')
 # Summaries.
 size=cc.groupby('kub_size_v1').detected_unetpp.agg(GT='size',Detected='sum').reset_index(); size['Missed']=size.GT-size.Detected; size['Recall']=size.Detected/size.GT; save(size,'phase11_kub_size_failure_summary.csv',True)
 tax=[]
 for name,mask in labels: tax.append({'Failure_Type':name,'Count':int(mask.sum()),'Rate':float(mask.mean())})
 for size_name in ['TINY','SMALL','MEDIUM','LARGE']:
  row=size[size.kub_size_v1==size_name].iloc[0]; tax.append({'Failure_Type':f'MISSED_{size_name}_ORIGINAL_COMPONENT','Count':int(row.Missed),'Rate':float(row.Missed/row.GT)})
 for cls,count in multi_table.detection_class.value_counts().items(): tax.append({'Failure_Type':f'MULTI_{cls}','Count':int(count),'Rate':float(count/len(multi_table))})
 summary=pd.DataFrame(tax); save(summary,'phase11_kub_failure_summary.csv',True)
 cutoffs={'low_dice_decile':{'cutoff':low,'comparison':'dice <= cutoff','n':int(x.low_dice_decile.sum())},'high_hd95_decile':{'cutoff':high_hd,'comparison':'valid hd95 >= cutoff','n':int(x.high_hd95_decile.sum())},'high_fp_decile':{'cutoff':high_fp,'comparison':'fp evaluation components >= cutoff','n':int(x.high_fp_decile.sum())},'label':'descriptive failure-analysis strata; not tuning or deployment thresholds'}; (A/'phase11_failure_strata_definitions.json').write_text(json.dumps(cutoffs,indent=2),encoding='utf-8')
 print(json.dumps(cutoffs,indent=2)); print(size.to_string(index=False)); print(multi_table.detection_class.value_counts()); print(overlap.to_string(index=False)); print('patients',len(patient))

if __name__=='__main__': main()
