import requests
import json
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Live AWS Function URL:
LAMBDA_URL = "https://rh3tpejwo2iyov7nmgrtfomyji0sohry.lambda-url.us-east-1.on.aws/"

def print_result(title, res_json):
    print("=" * 65)
    print(f"[{title}]")
    print("=" * 65)
    print(f"🔋 Vehicle / Pack ID : {res_json.get('battery_id')}")
    print(f"📊 Health Grade      : {res_json.get('health_grade')}")
    print(f"🔄 Predicted RUL     : {res_json.get('predicted_rul_cycles')} cycles")
    
    sentry = res_json.get("battery_sentry")
    if sentry:
        print("\n🛡️  --- BATTERYSENTRY COPILOT DIAGNOSTICS ---")
        print(f"   • Thermal Risk Score : {sentry.get('risk_score')}% ({sentry.get('threat_level')})")
        print(f"   • Ambient Climate    : {sentry.get('ambient_temp_c')} °C")
        bms = sentry.get("bms_recommendation", {})
        print(f"   • Max Charge Rate    : {bms.get('max_charging_rate')}")
        print(f"   • Cut-off Limit      : {bms.get('cutoff_soc')}")
        print(f"   • Cycles Salvaged    : +{bms.get('projected_cycles_saved')} cycles")
        print(f"   • Copilot Directive  : {sentry.get('agent_directive')}")
        print(f"   • Copilot Engine     : {'Google Gemini Flash' if sentry.get('gemini_powered') else 'Physics Rules'}")
    else:
        print("\n⚠️ BatterySentry payload not returned by remote endpoint (old deploy).")
    print("\nFull JSON Response:\n" + json.dumps(res_json, indent=2))

# --- TEST 1: HEALTHY BATTERY ---
healthy_battery = {
    "battery_id": "TATA-NEXON-001",
    "Discharge Time (s)": 2112.7,
    "Max. Voltage Dischar. (V)": 4.00,
    "Min. Voltage Charg. (V)": 3.43,
    "Time at 4.15V (s)": 4766.4,
    "Time constant current (s)": 5732.3,
    "Charging time (s)": 9054.6
}

try:
    r1 = requests.post(LAMBDA_URL, json=healthy_battery, timeout=6)
    print_result("TEST 1: HEALTHY BATTERY (EXPECT GRADE A)", r1.json())
except Exception as e:
    print(f"Remote test error: {e}")

# --- TEST 2: DEGRADED BATTERY ---
degraded_battery = {
    "battery_id": "USED-OLA-PACK-999",
    "Discharge Time (s)": 945.6,
    "Max. Voltage Dischar. (V)": 3.79,
    "Min. Voltage Charg. (V)": 3.70,
    "Time at 4.15V (s)": 1272.9,
    "Time constant current (s)": 1880.3,
    "Charging time (s)": 7460.4
}

try:
    r2 = requests.post(LAMBDA_URL, json=degraded_battery, timeout=6)
    print_result("TEST 2: DEGRADED BATTERY (EXPECT GRADE C + HIGH THERMAL RISK)", r2.json())
except Exception as e:
    print(f"Remote test error: {e}")