import os
import pandas as pd

def audit_directory(root_path):
    data = []
    for root, dirs, files in os.walk(root_path):
        for file in files:
            filepath = os.path.join(root, file)
            ext = os.path.splitext(file)[1]
            data.append({'root': root, 'file': file, 'extension': ext, 'path': filepath})
    return pd.DataFrame(data)

internal_root = r'D:\Softfors\omni_seg\data_raw'
external_root = r'D:\Softfors\final\external_test_ds'

internal_df = audit_directory(internal_root)
external_df = audit_directory(external_root)

print('Internal structure levels:')
print(internal_df['root'].value_counts())
print('\nExternal structure levels:')
print(external_df['root'].value_counts())
