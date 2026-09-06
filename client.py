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
    "Discharge Time (s)": 1420.5,
    "Max. Voltage Dischar. (V)": 4.21,
    "Min. Voltage Charg. (V)": 3.10,
    "Time at 4.15V (s)": 620.0,
    "Time constant current (s)": 1950.0,
    "Charging time (s)": 2850.0
}
r1 = requests.post(LAMBDA_URL, json=healthy_battery)
print(json.dumps(r1.json(), indent=2))

# --- TEST 2: DEGRADED BATTERY (TRIGGERS EMAIL) ---
print("\n" + "=" * 60)
print("🧪 TEST 2: GRADING A DEGRADED BATTERY (EXPECT GRADE C + EMAIL ALERT)")
print("=" * 60)
degraded_battery = {
    "battery_id": "USED-OLA-PACK-999",
    "Discharge Time (s)": 450.0,
    "Max. Voltage Dischar. (V)": 3.75,
    "Min. Voltage Charg. (V)": 2.45,
    "Time at 4.15V (s)": 45.0,
    "Time constant current (s)": 400.0,
    "Charging time (s)": 850.0
}
r2 = requests.post(LAMBDA_URL, json=degraded_battery)
print(json.dumps(r2.json(), indent=2))