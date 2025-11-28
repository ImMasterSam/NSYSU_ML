"""
地點合併工具 - 根據座標自動分群，並產生建議的合併規則
"""

import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist

# 載入資料
df_coords = pd.read_csv('../../data_after_process/unique_locations.csv', encoding='utf-8-sig')
print(f"📍 原始地點數: {len(df_coords)}")
print("\n原始地點列表:")
for i, row in df_coords.iterrows():
    print(f"  {i+1}. {row['Location']}")

# 計算 Haversine 距離 (公尺)
def haversine(coord1, coord2):
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return 6371000 * 2 * np.arcsin(np.sqrt(a))

# 準備座標矩陣
coords = df_coords[['Latitude', 'Longitude']].values
locations = df_coords['Location'].tolist()

# 計算距離矩陣
n = len(coords)
dist_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(i+1, n):
        d = haversine(coords[i], coords[j])
        dist_matrix[i, j] = d
        dist_matrix[j, i] = d

print(f"\n📏 距離範圍: {dist_matrix[dist_matrix > 0].min():.0f}m ~ {dist_matrix.max():.0f}m")

# 使用階層式分群 (Hierarchical Clustering)
# 設定不同的距離閾值
thresholds = [50, 100, 150, 200]

print("\n" + "=" * 70)
print("🔍 自動分群建議 (根據不同距離閾值)")
print("=" * 70)

for threshold in thresholds:
    # 使用 complete linkage (最遠距離)
    condensed_dist = pdist(coords, metric=lambda u, v: haversine(u, v))
    Z = linkage(condensed_dist, method='complete')
    clusters = fcluster(Z, t=threshold, criterion='distance')
    
    n_clusters = len(set(clusters))
    print(f"\n📦 閾值 {threshold}m → {n_clusters} 個群組")
    
    # 顯示每個群組
    cluster_dict = {}
    for loc, c in zip(locations, clusters):
        if c not in cluster_dict:
            cluster_dict[c] = []
        cluster_dict[c].append(loc)
    
    for c, locs in sorted(cluster_dict.items()):
        if len(locs) > 1:
            print(f"   群組 {c}: {', '.join(locs[:3])}{'...' if len(locs) > 3 else ''} ({len(locs)} 個)")

# 產生 100m 閾值的詳細分群結果
print("\n" + "=" * 70)
print("📋 建議合併規則 (100m 閾值，你可以手動調整)")
print("=" * 70)

condensed_dist = pdist(coords, metric=lambda u, v: haversine(u, v))
Z = linkage(condensed_dist, method='complete')
clusters = fcluster(Z, t=100, criterion='distance')

# 建立分群結果
cluster_dict = {}
for loc, c in zip(locations, clusters):
    if c not in cluster_dict:
        cluster_dict[c] = []
    cluster_dict[c].append(loc)

# 產生 CSV 格式的規則
rules = []
for c, locs in sorted(cluster_dict.items()):
    # 用第一個地點名稱作為區域名稱，或者你可以自己命名
    zone_name = locs[0] if len(locs) == 1 else f"Zone_{c}"
    for loc in locs:
        rules.append({
            'Original_Location': loc,
            'Zone_ID': c,
            'Zone_Name': zone_name,
            'Locations_in_Zone': len(locs)
        })

df_rules = pd.DataFrame(rules)
df_rules.to_csv('location_rules.csv', index=False, encoding='utf-8-sig')

print("\n✅ 已產生 location_rules.csv，內容如下：")
print(df_rules.to_string())

print("\n" + "=" * 70)
print("📝 下一步")
print("=" * 70)
print("""
1. 打開 location_rules.csv
2. 修改 Zone_Name 欄位，給每個區域取一個有意義的名稱
3. 例如：
   - 「理學院」、「工學院」、「管院」
   - 「行政大樓區」、「體育館區」
   - 「第一停車場」、「第二停車場」

4. 如果你覺得某些地點不應該合併，可以給它獨立的 Zone_ID

5. 完成後執行 violation_network_v3_zone.py 來訓練區域模型
""")
