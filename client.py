import requests
import json

# ⚠️ YOUR LIVE AWS FUNCTION URL:
LAMBDA_URL = "https://rh3tpejwo2iyov7nmgrtfomyji0sohry.lambda-url.us-east-1.on.aws/"

# --- TEST 1: HEALTHY BATTERY ---
print("=" * 60)
print("🧪 TEST 1: GRADING A HEALTHY BATTERY (EXPECT GRADE A)")
print("=" * 60)
healthy_battery = {
    "battery_id": "TATA-NEXON-001",
    "Discharge Time (s)": 2112.7,
    "Max. Voltage Dischar. (V)": 4.00,
    "Min. Voltage Charg. (V)": 3.43,
    "Time at 4.15V (s)": 4766.4,
    "Time constant current (s)": 5732.3,
    "Charging time (s)": 9054.6
}
r1 = requests.post(LAMBDA_URL, json=healthy_battery)
print(json.dumps(r1.json(), indent=2))

# --- TEST 2: DEGRADED BATTERY (TRIGGERS EMAIL) ---
print("\n" + "=" * 60)
print("🧪 TEST 2: GRADING A DEGRADED BATTERY (EXPECT GRADE C + EMAIL ALERT)")
print("=" * 60)
degraded_battery = {
    "battery_id": "USED-OLA-PACK-999",
    "Discharge Time (s)": 945.6,
    "Max. Voltage Dischar. (V)": 3.79,
    "Min. Voltage Charg. (V)": 3.70,
    "Time at 4.15V (s)": 1272.9,
    "Time constant current (s)": 1880.3,
    "Charging time (s)": 7460.4
}
r2 = requests.post(LAMBDA_URL, json=degraded_battery)
print(json.dumps(r2.json(), indent=2))