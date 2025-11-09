import fastf1

import os

# 檢查並建立 cache 資料夾
if not os.path.exists('.cache'):
    os.makedirs('.cache')

fastf1.set_log_level('ERROR')
fastf1.Cache.enable_cache('.cache')

YEAR = 2025
RACE = 20 # Mexico
SESSION = 'R'

session = fastf1.get_session(YEAR, RACE, SESSION)
session.load(laps=True, telemetry=False, weather=True, messages=False)

print(session.session_info['Meeting']['OfficialName'])
print(session.results[['Position', 'Abbreviation', 'Points']])