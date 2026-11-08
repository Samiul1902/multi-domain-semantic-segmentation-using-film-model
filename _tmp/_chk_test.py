import csv, collections, pathlib
val = list(csv.DictReader(open('manifests/phase4_v3/val.csv', encoding='utf-8')))
test = list(csv.DictReader(open('manifests/phase4_v3/test.csv', encoding='utf-8')))
print('VAL rows', len(val), 'TEST rows', len(test))
c = collections.Counter()
for r in val:
    if r['dataset'] == 'ISIC':
        p = r['gt_mask_path']
        for tag in ('Task1_Validation_GroundTruth', 'Task1_Training_GroundTruth', 'Task1_Test_GroundTruth'):
            if tag in p:
                c[tag] += 1
print('VAL ISIC gt folders:', dict(c))
ct = collections.Counter()
for r in test:
    if r['dataset'] == 'ISIC':
        for tag in ('Task1_Validation_GroundTruth', 'Task1_Training_GroundTruth', 'Task1_Test_GroundTruth'):
            if tag in r['gt_mask_path']:
                ct[tag] += 1
print('TEST ISIC gt folders:', dict(ct))
vid = {r['sample_id'] for r in val}
tid = {r['sample_id'] for r in test}
print('VAL n sample_id', len(vid), 'TEST n', len(tid), 'OVERLAP', len(vid & tid))
# Are the two ISIC samples from the Test folder present in TEST?
for sid in ('e3a6813878b2407c0c8c2e534de8d40a', 'e49371af49edbb17500da84dd2adf3df'):
    print(sid, 'in VAL', sid in vid, 'in TEST', sid in tid)
