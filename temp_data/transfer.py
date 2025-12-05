import pandas as pd

# 讀取 CSV 檔案
year = 2023
file_path = f'./{year}.csv'
df = pd.read_csv(file_path, encoding='utf-8')

# 提取月份名稱
months = df.columns[1:]

# 初始化結果列表
result = []

# 遍歷每一行資料
for index, row in df.iterrows():
    if row["日/月"] == "平均":  # 跳過平均行
        continue
    day = row["日/月"]
    for month in months:
        value = row[month]
        if value != "--":  # 跳過缺失值
            date = f"{year}-{int(month):02d}-{int(day):02d}"
            result.append([date, float(value)])

# 轉換為 DataFrame
result_df = pd.DataFrame(result, columns=["date", "temperature"])

# 儲存為 CSV
output_path = f'./temperature_{year}.csv'
result_df.to_csv(output_path, index=False, encoding='utf-8')

print(f"轉換完成，結果已儲存至 {output_path}")