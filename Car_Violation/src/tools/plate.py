import pandas as pd

# 1. 讀取清洗後的資料
input_filename = '../../data_after_process/violate_cleaned.csv'
try:
    with open(input_filename, 'r', encoding='utf-8-sig') as f:
        df = pd.read_csv(f)
    print(f"成功讀取 {input_filename}，共 {len(df)} 筆資料。")
except FileNotFoundError:
    print(f"找不到檔案 {input_filename}，請確認檔名是否正確。")
    exit()

# ==========================================
# 邏輯 A: 車牌規則辨識 (V5 - 備用)
# ==========================================
def classify_by_plate_v5(plate):
    if pd.isna(plate):
        return "Other"
    
    raw = str(plate).strip().replace('-', '').replace(' ', '').upper()
    length = len(raw)
    
    alphas = sum(c.isalpha() for c in raw)
    digits = sum(c.isdigit() for c in raw)
    
    if length == 0:
        return "Other"

    # --- 7 碼 ---
    if length == 7:
        if alphas == 2: return "Scooter" # 特殊 2英文
        first_char = raw[0]
        if first_char in ['M', 'N', 'P', 'Q', 'W', 'L', 'E']: return "Scooter"
        else: return "Car"

    # --- 6 碼 ---
    elif length == 6:
        if alphas == 3 and digits == 3: return "Scooter"
        elif alphas == 2 and digits == 4:
            # 檢查是否為標準頭尾分開 (AAxxxx / xxxxAA) -> Car
            is_std_start = raw[0].isalpha() and raw[1].isalpha()
            is_std_end = raw[-1].isalpha() and raw[-2].isalpha()
            if is_std_start or is_std_end: return "Car"
            else: return "Scooter" # 穿插 -> Scooter
        elif alphas == 1 and digits == 5: return "Car" # 特殊汽車
        else: return "Other"

    else: return "Other"

# ==========================================
# 邏輯 B: 混合判斷主函數 (序號優先)
# ==========================================
def determine_vehicle_type(row):
    # 1. 取得序號與車牌
    sid = str(row['序號']).strip()
    plate = str(row['車牌號碼']).strip()

    # 2. 檢查是否為新式序號 (數字開頭，且長度足夠)
    # 格式範例: 2511211549130810Z3 (18碼)
    # 前10碼是時間(YYMMDDHHMM)，第11碼(Index 10)是車種代號
    is_new_style = (len(sid) >= 11) and (sid[0].isdigit())

    if is_new_style:
        # 提取第 11 碼 (Index 10)
        type_indicator = sid[10]
        
        if type_indicator == '1':
            return "Scooter" # 序號指定為機車
        elif type_indicator == '2':
            return "Car"     # 序號指定為汽車
        else:
            # 若第 11 碼不是 1 或 2，退回用車牌判斷
            return classify_by_plate_v5(plate)
    else:
        # 舊式序號 -> 使用車牌規則
        return classify_by_plate_v5(plate)

# 3. 應用函數
# 這裡使用 axis=1 因為我們需要同時讀取 '序號' 和 '車牌號碼'
print("正在依照「序號優先」規則進行分類...")
df['Vehicle_Type'] = df.apply(determine_vehicle_type, axis=1)

# 4. 分流資料
valid_data = df[df['Vehicle_Type'] != 'Other']
wrong_plate_data = df[df['Vehicle_Type'] == 'Other']

# 5. 存檔
output_valid = 'violate_with_type.csv'
valid_data.to_csv(output_valid, index=False, encoding='utf-8-sig')

output_wrong = 'wrong_plate.csv'
wrong_plate_data.to_csv(output_wrong, index=False, encoding='utf-8-sig')

print("-" * 30)
print("處理完成！(序號判斷優先: 1=機車, 2=汽車)")
print(f"1. 有效資料 '{output_valid}':")
print(f"   - Car (汽車): {len(valid_data[valid_data['Vehicle_Type'] == 'Car'])} 筆")
print(f"   - Scooter (機車): {len(valid_data[valid_data['Vehicle_Type'] == 'Scooter'])} 筆")
print(f"2. 異常/無法辨識資料 '{output_wrong}': {len(wrong_plate_data)} 筆")