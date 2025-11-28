import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import os
import warnings

# ==========================================
# 1. 環境設定
# ==========================================
warnings.filterwarnings('ignore')
cache_dir = './f1_cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)

class StrategyGainPredictor:
    def __init__(self, year=2023):
        self.year = year
        self.dataset = None
        self.model = None
        
        # === 輔助資料集 (Supplementary Dataset) [cite: 12] ===
        # 這是我們手動引入的"外部資料"，用來增強模型
        # 定義賽道特性：1=High Deg (高磨損), 2=Medium, 3=Low (低磨損)
        # 資料來源：Pirelli 賽前報告 / 網路資料
        self.circuit_info = {
            'Bahrain': {'Degradation': 1, 'Type': 'Permanent'},
            'Saudi Arabia': {'Degradation': 2, 'Type': 'Street'},
            'Australia': {'Degradation': 2, 'Type': 'Street-Hybrid'},
            'Miami': {'Degradation': 2, 'Type': 'Street'},
            'Spain': {'Degradation': 1, 'Type': 'Permanent'},
            'Austria': {'Degradation': 2, 'Type': 'Permanent'},
            'British': {'Degradation': 1, 'Type': 'Permanent'},
            'Hungary': {'Degradation': 2, 'Type': 'Permanent'},
            'Belgium': {'Degradation': 1, 'Type': 'Permanent'},
            'Dutch': {'Degradation': 1, 'Type': 'Permanent'},
            'Italian': {'Degradation': 3, 'Type': 'Permanent'},
            'Singapore': {'Degradation': 1, 'Type': 'Street'},
            'Japanese': {'Degradation': 1, 'Type': 'Permanent'},
            'Qatar': {'Degradation': 1, 'Type': 'Permanent'},
            'United States': {'Degradation': 2, 'Type': 'Permanent'},
            'Las Vegas': {'Degradation': 3, 'Type': 'Street'}
        }

    def build_dataset(self):
        print(f"🚀 開始構建 {self.year} 賽季資料集 (FastF1 + Circuit Info)...")
        
        target_races = list(self.circuit_info.keys())
        all_data = []

        for gp in target_races:
            print(f"\n📍 分析賽站: {gp}")
            try:
                # 載入數據 (開啟 weather=True)
                session = fastf1.get_session(self.year, gp, 'R')
                session.load(telemetry=False, messages=False)
                
                # 1. 獲取 FastF1 內建天氣數據 (解決 NONE 問題)
                laps = session.laps
                # 將天氣數據合併到每一圈
                weather_data = laps.get_weather_data()
                laps = laps.reset_index(drop=True)
                # 這裡我們只取需要的欄位合併
                if not weather_data.empty:
                    weather_cols = weather_data[['TrackTemp', 'AirTemp', 'Humidity']]
                    laps = pd.concat([laps, weather_cols], axis=1)
                else:
                    print(f"   ⚠️ 警告: {gp} 無法獲取內建天氣，使用預設值")
                    laps['TrackTemp'] = 35.0
                
                # 只保留綠旗
                laps = laps[laps['TrackStatus'] == '1']
                
                # 2. 獲取輔助資料 (Supplementary Data Integration)
                deg_level = self.circuit_info[gp]['Degradation']
                is_street = 1 if 'Street' in self.circuit_info[gp]['Type'] else 0
                
                pit_stops = session.laps[~pd.isna(session.laps['PitInTime'])]
                
                print(f"   🏎️ 掃描 {len(pit_stops)} 次進站...")
                
                for i, stop in pit_stops.iterrows():
                    driver = stop['Driver']
                    stop_lap = int(stop['LapNumber'])
                    
                    # 取得進站"前一圈"數據
                    prev_lap_data = laps[(laps['Driver'] == driver) & (laps['LapNumber'] == stop_lap - 1)]
                    if prev_lap_data.empty: continue
                    
                    # 取得進站"後三圈"數據
                    post_lap_data = laps[(laps['Driver'] == driver) & (laps['LapNumber'] == stop_lap + 3)]
                    if post_lap_data.empty: continue
                    
                    # === 提取特徵 ===
                    # 關鍵修正：確保 TrackTemp 是數值
                    track_temp = prev_lap_data['TrackTemp'].iloc[0]
                    if pd.isna(track_temp): track_temp = 35.0 # 最終保底
                    
                    pos_before = prev_lap_data['Position'].iloc[0]
                    pos_after = post_lap_data['Position'].iloc[0]
                    tyre_age = stop['TyreLife']
                    if pd.isna(tyre_age): tyre_age = 15
                    
                    try:
                        pit_duration = stop['PitDuration'].total_seconds()
                    except:
                        pit_duration = 25.0
                    
                    # Target: 排名沒有掉 (或提升)
                    is_success = 1 if pos_after <= pos_before else 0
                    
                    all_data.append({
                        'TrackTemp': float(track_temp), # 確保是 float
                        'Degradation': deg_level,       # Supp Data
                        'IsStreet': is_street,          # Supp Data
                        'TyreAge': tyre_age,
                        'PitDuration': pit_duration,
                        'PosBefore': pos_before,
                        'IsSuccess': is_success
                    })
                    
            except Exception as e:
                print(f"   ⚠️ 跳過此站: {e}")
                continue
                
        self.dataset = pd.DataFrame(all_data)
        
        # 去除極端異常值
        self.dataset = self.dataset.dropna()
        
        print("\n" + "="*30)
        if not self.dataset.empty:
            print(f"🎉 資料集完成！共 {len(self.dataset)} 筆")
            print(f"   - 溫度範圍: {self.dataset['TrackTemp'].min()}°C ~ {self.dataset['TrackTemp'].max()}°C")
            print(f"   - 成功案例: {self.dataset['IsSuccess'].sum()}")
        else:
            print("❌ 錯誤：沒有數據。")

    def train_model(self):
        if self.dataset is None or self.dataset.empty: return
        
        print("\n🤖 訓練模型 (Balanced Random Forest)...")
        
        # 特徵工程
        X = self.dataset[['TrackTemp', 'Degradation', 'TyreAge', 'PitDuration', 'PosBefore']]
        y = self.dataset['IsSuccess']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 關鍵修正：class_weight='balanced' 解決不平衡問題
        self.model = RandomForestClassifier(n_estimators=100, 
                                            random_state=42, 
                                            class_weight='balanced')
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_test)
        
        print(f"🏆 模型準確率 (Accuracy): {accuracy_score(y_test, y_pred):.2%}")
        print("\n📊 分類報告 (注意 Class 1 的 Recall 是否提升):")
        print(classification_report(y_test, y_pred))
        
        self.plot_results()

    def plot_results(self):
        # 畫圖：溫度對成功率的影響
        # 使用 jitter 避免點重疊，並檢查數據變異性
        df = self.dataset
        
        if df['TrackTemp'].std() < 0.1:
            print("⚠️ 溫度數據無變化，跳過繪圖。")
            return

        plt.figure(figsize=(10, 6))
        # Logistic Regression Curve
        try:
            sns.regplot(x='TrackTemp', y='IsSuccess', data=df, 
                        logistic=True, ci=None, 
                        scatter_kws={'alpha': 0.3}, line_kws={'color': 'red'})
        except:
            sns.scatterplot(x='TrackTemp', y='IsSuccess', data=df, alpha=0.3)
            
        plt.title('Impact of Track Temperature on Strategy Success')
        plt.xlabel('Track Temperature (°C)')
        plt.ylabel('Probability of Maintaining Position')
        plt.show()
        print("💡 圖表已生成。紅色曲線若上升，代表高溫有利於進站策略(因對手衰退快)。")

# --- 執行 ---
if __name__ == "__main__":
    predictor = StrategyGainPredictor(2023)
    predictor.build_dataset()
    predictor.train_model()