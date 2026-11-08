import csv, pathlib, sys
sys.path.insert(0, r"D:/Softfors/jup")
ps = list(csv.DictReader(open('full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv', encoding='utf-8')))
man = {r['sample_id']: r for r in csv.DictReader(open('reports/tables/phase21_prediction_manifest.csv', encoding='utf-8'))}
for dom in ('ISIC','BUSI','KVASIR','KUB'):
    ids = [r['sample_id'] for r in ps if r['domain']==dom and r['sample_id'] in man]
    ids.sort(key=lambda s: float([r for r in ps if r['sample_id']==s][0]['delta_dice']))
    for tag, sid in (('worst', ids[0]), ('best', ids[-1])):
        gt = man[sid]['gt_mask_path']
        print(dom, tag, sid, '| gt exists:', pathlib.Path(gt).exists())
        print('   gt:', gt)
