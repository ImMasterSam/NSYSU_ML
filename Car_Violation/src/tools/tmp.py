import pandas as pd
import numpy as np
import random

# ==========================================
# 1. 讀取與基礎清洗
# ==========================================
input_file = '../../data_after_process/violate_with_type.csv'
try:
    df = pd.read_csv(input_file, encoding='utf-8-sig')
except:
    df = pd.read_csv(input_file, encoding='cp950', errors='replace')

# 關鍵修正：不再篩選 Top 10，而是保留所有地點
# 移除空白並確保是字串
df['Location_Clean'] = df['違規地點'].astype(str).str.strip()

# 移除空值或無效地點
df = df[df['Location_Clean'] != 'nan']
df = df[df['Location_Clean'] != '']

print(f"偵測到全校共有 {len(df['Location_Clean'].unique())} 個獨特違規地點。")
unique_locations = df['Location_Clean'].unique()
print(len(unique_locations))
print(unique_locations)

# 將所有獨特地點輸出成一個欄位的 CSV
output_df = pd.DataFrame({'Location_Clean': unique_locations})
output_df.to_csv('unique_locations.csv', index=False, encoding='utf-8-sig')

