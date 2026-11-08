import csv, pathlib, sys
sys.path.insert(0, r"D:/Softfors/jup")
rows = list(csv.DictReader(open('reports/tables/phase21_prediction_manifest.csv', encoding='utf-8')))
seen = set()
for r in rows:
    d = r['dataset']
    if d in seen: continue
    seen.add(d)
    s = r['gt_mask_path']
    if d == 'ISIC':
        c = s.replace('_segmentation.png', '.jpg').replace('Task1_Training_GroundTruth', 'Task1-2_Training_Input').replace('Task1_Validation_GroundTruth', 'Task1-2_Validation_Input')
    elif d == 'BUSI':
        c = s.replace('\\gt\\', '\\img\\').replace('_anno.bmp', '.bmp')
    elif d == 'KVASIR':
        c = s.replace('\\masks\\', '\\images\\')
    else:
        c = s.replace('\\Masks\\', '\\Images\\').replace('_mask.png', '.png')
    print(d, '| gt:', pathlib.Path(s).name, '| img:', pathlib.Path(c).name, 'EXISTS' if pathlib.Path(c).exists() else 'MISSING')
