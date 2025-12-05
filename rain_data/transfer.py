import xml.etree.ElementTree as ET
import csv

year = 2022

xml_file = f"./raw_data/{year}.xml"
output_file = f"./csv_data/{year}.csv"

tree = ET.parse(xml_file)
root = tree.getroot()

ns = {"cwa": "urn:cwa:gov:tw:cwacommon:0.1"}

rows = []

# 找到所有 location
locations = root.findall(".//cwa:location", ns)

for loc in locations:
    station = loc.find("cwa:station", ns)
    if station is None:
        continue

    name = station.find("cwa:StationName", ns).text

    # 只取高雄
    if name == "高雄":
        # 找該測站下所有日期與降水量
        times = loc.findall(".//cwa:stationObsTime", ns)

        for t in times:
            date = t.find("cwa:Date", ns).text
            precip = t.find("cwa:weatherElements/cwa:Precipitation", ns).text
            rows.append([date, precip])

# 寫入 CSV
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "Precipitation"])
    writer.writerows(rows)

print(f"完成！已輸出 {output_file}")
