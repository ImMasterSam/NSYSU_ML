import random
import requests
import pandas as pd
import time
import urllib3 # 用來處理警告訊息

# 【修正 1】關閉 SSL 不安全連線的警告訊息 (讓輸出畫面乾淨一點)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定基礎網址
base_url = "https://vehicle.nsysu.edu.tw/ViolateList.php"

# 設定 Headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # 請確認這邊填入正確的 PHPSESSID=...
    "Cookie": "PHPSESSID=42te16c12kas2uh5ol3gikddf7" 
}

all_dfs = []

# 測試爬取前 3 頁
for page in range(1500, 2169):
    params = {
        "item_id": "115",
        "system": "ep",
        "app_violationPageSize": "50",
        "app_violationPage": page,
        "lang": "zh-tw"
    }
    
    print(f"正在爬取第 {page} 頁...")
    
    try:
        # 【修正 2】加入 verify=False 以略過 SSL 憑證檢查
        response = requests.get(base_url, params=params, headers=headers, verify=False)
        
        # 檢查是否被登出
        if "使用者登入" in response.text or "帳號" in response.text and "違規紀錄" not in response.text:
            print(f"警報：第 {page} 頁似乎被導向登入頁面，請檢查 Cookie 是否過期。")
            break
            
        dfs = pd.read_html(response.text, attrs={'id': 'Contentapp_violation'}, header=1)
        
        if dfs:
            df = dfs[0]
            if len(df) > 0:
                all_dfs.append(df)
            
    except Exception as e:
        print(f"第 {page} 頁發生錯誤: {e}")
        
    # sleep_time = random.uniform(3, 6) # 隨機休息 3 到 6 秒
    # print(f"休息 {sleep_time:.2f} 秒...")
    # time.sleep(0.5)

# 合併並儲存
if all_dfs:
    final_df = pd.concat(all_dfs, ignore_index=True)
    print(f"爬取完成！共 {len(final_df)} 筆資料")
    final_df.to_excel("中山大學違規紀錄總表10.xlsx", index=False)
else:
    print("沒有抓取到任何資料。")