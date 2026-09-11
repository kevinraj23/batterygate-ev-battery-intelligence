# lambda_function.py
import json
import os
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from decimal import Decimal

# Pure Python model
from model_code import score

# -------------------------------------------------------------
# ⚠️ CONFIGURATION: Automatically loaded from local .env or
# via AWS Lambda Environment Variable "GEMINI_API_KEY"
# -------------------------------------------------------------
if not os.environ.get("GEMINI_API_KEY"):
    try:
        _env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(_env_path):
            with open(_env_path, "r", encoding="utf-8") as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line and not _line.startswith("#") and "=" in _line:
                        _k, _v = _line.split("=", 1)
                        os.environ.setdefault(_k.strip(), _v.strip())
    except Exception:
        pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

FEATURES = [
    "Discharge Time (s)", 
    "Max. Voltage Dischar. (V)",
    "Min. Voltage Charg. (V)", 
    "Time at 4.15V (s)",
    "Time constant current (s)", 
    "Charging time (s)"
]

TABLE_NAME = os.environ.get("TABLE_NAME", "BatteryReports")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

try:
    import boto3
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(TABLE_NAME)
except Exception as _boto_err:
    boto3 = None
    table = None


# =============================================================
# 🌡️ TOOL 1: Free Ambient Climate Telemetry (Open-Meteo)
# =============================================================
def get_ambient_temperature(lat=13.0827, lon=80.2707):
    """
    Fetches real-time ambient temperature via Open-Meteo API.
    100% Free, requires no API key, zero sign-up.
    Default coordinates: 13.0827, 80.2707 (Chennai, India EV hub).
    """
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
        req = urllib.request.Request(url, headers={"User-Agent": "BatteryGate-Sentry/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                payload = json.loads(resp.read().decode("utf-8"))
                temp = float(payload.get("current", {}).get("temperature_2m", 35.0))
                return round(temp, 1)
    except Exception as e:
        print(f"⚠️ Open-Meteo weather fetch fallback: {e}")
    return 35.0  # Default tropical baseline temperature


# =============================================================
# 🧠 TOOL 2: Google Gemini AI Reasoning Copilot
# =============================================================
def call_gemini_sentry(prompt, api_key):
    """
    Direct zero-dependency call to Google Gemini 2.0 / 1.5 Flash via urllib.
    Requires no pip packages, executing natively in AWS Lambda.
    """
    if not api_key or api_key.strip() in ("", "AIzaSyYourCopiedKeyHere"):
        return None

    # Try gemini-2.0-flash first, fallback to gemini-1.5-flash
    models = ["gemini-2.0-flash", "gemini-1.5-flash"]
    for model in models:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 220
            }
        }
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
        except Exception as err:
            print(f"⚠️ Gemini ({model}) call error: {err}")
            continue

    return None


# =============================================================
# 🛡️ BATTERYSENTRY: Autonomous Thermal Runaway & Lifespan Agent
# =============================================================
def run_battery_sentry(features, rul, grade, battery_id, ambient_temp, user_gemini_key=None):
    """
    Autonomous agent assessing thermal runaway risk, cell impedance, and
    prescribing customized BMS throttling to maximize lifespan.
    """
    dis_time = features[0]   # Discharge Time (s)
    max_v = features[1]      # Max. Voltage Dischar. (V)
    time_415 = features[3]   # Time at 4.15V (s)
    chg_time = features[5]   # Charging time (s)

    # 1. Physics-based Risk Calculations
    # Internal resistance (R0) approximation based on voltage retention at 4.15V
    low_415_penalty = max(0, (2000 - time_415) / 45.0) if time_415 < 2000 else 0
    # Ambient heat stress factor (>25°C baseline)
    heat_stress = max(0, (ambient_temp - 25.0) * 2.8)
    # Aging factor (depleted RUL increases lithium plating probability on anode)
    aging_stress = max(0, (1133.0 - rul) / 13.0)

    raw_risk = heat_stress + low_415_penalty + aging_stress
    risk_score = int(min(98, max(5, round(raw_risk))))

    # 2. Derive Adaptive BMS Thresholds
    if risk_score >= 70 or "Grade C" in grade:
        threat_level = "CRITICAL (High Lithium Plating / Thermal Hazard)"
        throttle_kw = "Max 15 kW (Slow AC Only · Inhibit DC Fast Charge)"
        cutoff_soc = "75% SoC"
        cycles_saved = 180
    elif risk_score >= 40 or "Grade B" in grade:
        threat_level = "ELEVATED (Thermal Stress · Impedance Rise)"
        throttle_kw = "Max 30 kW (Throttled DC Fast Charge)"
        cutoff_soc = "80% SoC"
        cycles_saved = 115
    else:
        threat_level = "OPTIMAL (Safe Thermal Operational Window)"
        throttle_kw = "Full 50 kW Supported (Standard Fast Charge)"
        cutoff_soc = "90% SoC"
        cycles_saved = 40

    # 3. Gemini Copilot Reasoning
    active_key = user_gemini_key if (user_gemini_key and len(user_gemini_key) > 10) else GEMINI_API_KEY
    gemini_directive = None

    if active_key:
        prompt = (
            f"You are BatterySentry, an autonomous EV battery safety and lifespan copilot.\n"
            f"Vehicle: {battery_id}\n"
            f"Health: {grade}, Remaining Useful Life: {rul:.1f} cycles.\n"
            f"Ambient Climate: {ambient_temp}°C.\n"
            f"Thermal Runaway Risk Score: {risk_score}% ({threat_level}).\n"
            f"BMS Action: Cap charging rate to '{throttle_kw}' and terminate charge at '{cutoff_soc}'.\n"
            f"Projected Lifespan Salvage: ~{cycles_saved} cycles.\n"
            f"Write a concise, professional 2-sentence technical directive to the technician/driver "
            f"explaining the physical reason for this throttling and how it preserves the pack."
        )
        gemini_directive = call_gemini_sentry(prompt, active_key)

    # 4. Fallback Rule Engine (If Gemini key is empty or offline)
    if not gemini_directive:
        if risk_score >= 70:
            gemini_directive = (
                f"High ambient heat ({ambient_temp}°C) combined with reduced cell impedance creates elevated risk of anode lithium plating. "
                f"Throttling charge rate to {throttle_kw} and cutting off at {cutoff_soc} prevents thermal runaway and salvages ~{cycles_saved} cycles."
            )
        elif risk_score >= 40:
            gemini_directive = (
                f"Moderate degradation detected under {ambient_temp}°C ambient temperature. "
                f"Restricting DC fast charging to {throttle_kw} up to {cutoff_soc} minimizes cathode lattice stress, extending useful life by ~{cycles_saved} cycles."
            )
        else:
            gemini_directive = (
                f"Pack impedance is within healthy parameters at {ambient_temp}°C. Standard charging profile supported with normal cell balancing recommended."
            )

    return {
        "risk_score": risk_score,
        "threat_level": threat_level,
        "ambient_temp_c": ambient_temp,
        "bms_recommendation": {
            "max_charging_rate": throttle_kw,
            "cutoff_soc": cutoff_soc,
            "projected_cycles_saved": cycles_saved
        },
        "agent_directive": gemini_directive,
        "gemini_powered": bool(gemini_directive and active_key and active_key != "")
    }


def send_dynamic_email(recipient_email, battery_id, rul, grade, sentry=None):
    """Sends a professional HTML Battery Health Report with BatterySentry alert badge"""
    if not SENDER_EMAIL or not SENDER_PASSWORD or not recipient_email:
        return
    
    msg = MIMEMultipart()
    msg['From'] = f"EV Battery Health Cloud <{SENDER_EMAIL}>"
    msg['To'] = recipient_email
    
    badge_color = "#10b981" if "A (" in grade else ("#f59e0b" if "B (" in grade else "#ef4444")
    
    sentry_html = ""
    if sentry:
        risk_color = "#ef4444" if sentry["risk_score"] >= 70 else ("#f59e0b" if sentry["risk_score"] >= 40 else "#10b981")
        sentry_html = f"""
        <div style="margin-top: 20px; background-color: #0f172a; border-radius: 8px; padding: 16px; border: 1px solid #334155; color: #f8fafc;">
            <h4 style="margin: 0 0 10px 0; color: #38bdf8; font-size: 14px;">🛡️ BatterySentry™ Active Thermal Directive</h4>
            <table style="width: 100%; font-size: 13px; color: #cbd5e1; border-collapse: collapse;">
                <tr><td style="padding: 4px 0;"><b>Thermal Risk:</b></td><td style="color: {risk_color}; font-weight: bold;">{sentry['risk_score']}% — {sentry['threat_level']}</td></tr>
                <tr><td style="padding: 4px 0;"><b>Ambient Temp:</b></td><td>{sentry['ambient_temp_c']} °C</td></tr>
                <tr><td style="padding: 4px 0;"><b>BMS Throttle Limit:</b></td><td>{sentry['bms_recommendation']['max_charging_rate']}</td></tr>
                <tr><td style="padding: 4px 0;"><b>Cut-off SoC:</b></td><td>{sentry['bms_recommendation']['cutoff_soc']}</td></tr>
                <tr><td style="padding: 4px 0;"><b>Lifespan Extension:</b></td><td style="color: #4ade80;">+{sentry['bms_recommendation']['projected_cycles_saved']} Cycles</td></tr>
            </table>
            <p style="margin: 10px 0 0 0; font-size: 12px; color: #94a3b8; line-height: 1.5; border-top: 1px solid #1e293b; padding-top: 8px;">
                <b>Directive:</b> {sentry['agent_directive']}
            </p>
        </div>
        """

    msg['Subject'] = f"⚡ EV Battery Health & Sentry Report: {battery_id} ({grade.split(' ')[0]})"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f3f4f6; padding: 20px;">
        <div style="max-width: 580px; background: white; border-radius: 10px; padding: 25px; margin: auto; border: 1px solid #e5e7eb;">
            <h2 style="color: #1f2937; margin-top: 0;">🔋 EV Battery Diagnostic Certificate</h2>
            <p style="color: #4b5563;">Here is the real-time health analysis for vehicle: <b>{battery_id}</b></p>
            <div style="background-color: #f9fafb; border-left: 5px solid {badge_color}; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h3 style="margin: 0; color: {badge_color};">{grade}</h3>
                <h1 style="margin: 10px 0; color: #111827;">~{rul:.1f} <span style="font-size: 16px; color: #6b7280;">cycles remaining</span></h1>
            </div>
            {sentry_html}
            <table style="width: 100%; font-size: 14px; color: #374151; border-collapse: collapse; margin-top: 16px;">
                <tr><td style="padding: 6px 0;"><b>Report Generated:</b></td><td>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
                <tr><td style="padding: 6px 0;"><b>Cloud Provider:</b></td><td>AWS Lambda Serverless ML + Gemini Copilot</td></tr>
            </table>
            <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="font-size: 12px; color: #9ca3af; text-align: center;">Powered by HNEI Battery Degradation Benchmark &amp; BatterySentry</p>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=5)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Report successfully emailed to {recipient_email}")
    except Exception as e:
        print(f"⚠️ Email dispatch error: {e}")


# =============================================================
# 🚀 AWS LAMBDA ENTRYPOINT
# =============================================================
def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps({"message": "CORS OK"})
        }

    try:
        body = json.loads(event["body"]) if "body" in event and isinstance(event["body"], str) else event
        x = [float(body[f]) for f in FEATURES]
        battery_id = body.get("battery_id", "UNKNOWN-BATTERY")
        user_email = body.get("user_email", "").strip()
        user_gemini_key = body.get("gemini_api_key", "").strip()
        
        # 1. ML Inference (Hawaii Natural Energy Institute trained model)
        predicted_rul = float(score(x))
        
        if predicted_rul > 600:
            grade = "Grade A (Healthy - >80% SOH)"
        elif predicted_rul > 200:
            grade = "Grade B (Moderate - 60-80% SOH)"
        else:
            grade = "Grade C (Degraded - Replace/Recycle)"
            
        timestamp_str = datetime.now(timezone.utc).isoformat()

        # 2. Real-time Climate Telemetry (Open-Meteo)
        lat = float(body.get("latitude", 13.0827))
        lon = float(body.get("longitude", 80.2707))
        ambient_temp = float(body.get("ambient_temp", get_ambient_temperature(lat, lon)))

        # 3. Autonomous BatterySentry Agent Reasoning
        sentry = run_battery_sentry(
            features=x,
            rul=predicted_rul,
            grade=grade,
            battery_id=battery_id,
            ambient_temp=ambient_temp,
            user_gemini_key=user_gemini_key
        )
        
        # 4. DynamoDB Log
        if table is not None:
            try:
                table.put_item(
                    Item={
                        "battery_id": battery_id,
                        "timestamp": timestamp_str,
                        "predicted_rul": Decimal(str(round(predicted_rul, 1))),
                        "grade": grade,
                        "recipient_email": user_email,
                        "sentry_risk_score": Decimal(str(sentry["risk_score"])),
                        "sentry_threat_level": sentry["threat_level"],
                        "sentry_directive": sentry["agent_directive"]
                    }
                )
            except Exception as db_err:
                print(f"DynamoDB Error (non-blocking): {db_err}")
            
        # 5. Email Dispatch (Optional)
        if user_email:
            send_dynamic_email(user_email, battery_id, predicted_rul, grade, sentry)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "status": "SUCCESS",
                "battery_id": battery_id,
                "predicted_rul_cycles": round(predicted_rul, 1),
                "health_grade": grade,
                "battery_sentry": sentry,
                "email_dispatched_to": user_email if user_email else "None",
                "timestamp": timestamp_str
            })
        }

    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": f"Missing feature: {str(e)}", "required_features": FEATURES})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }
