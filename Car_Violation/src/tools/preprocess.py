import pandas as pd

print("正在讀取檔案並修正編碼問題...")

# 1. 使用 Python 內建的 open() 來開啟檔案
# 這樣我們可以使用 errors='replace' 來強制替換掉看不懂的亂碼 (0xf9)
with open('rawdata/violate.csv', 'r', encoding='big5', errors='replace') as f:
    # 2. 將處理過的檔案物件 f 丟給 read_csv
    # sep=None 與 engine='python' 讓它自動偵測分隔符號 (解決整行變字串的問題)
    df = pd.read_csv(f, sep=None, engine='python')

print(f"原始資料讀取成功！資料形狀: {df.shape}")
print("欄位名稱:", df.columns.tolist())

# --- 以下是原本的清洗邏輯 ---

# 定義要刪除的關鍵字
keyword = "每頁紀錄"

# 建立過濾器 (Mask)
mask = df.apply(lambda row: row.astype(str).str.contains(keyword).any(), axis=1)

# 刪除包含關鍵字的列
df_clean = df[~mask]

# (選用) 移除沒有聯絡人的空資料
# df_clean = df_clean.dropna(subset=['聯絡人'])

print(f"清洗後資料筆數: {len(df_clean)}")
print(f"共刪除了 {len(df) - len(df_clean)} 筆雜訊資料")

# 3. 儲存結果 (存成 utf-8-sig 以便 Excel 開啟)
output_filename = 'violate_cleaned.csv'
df_clean.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"處理完成！已儲存為 {output_filename}")