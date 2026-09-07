# lambda_function.py
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from decimal import Decimal
import boto3

# Pure Python model
from model_code import score

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

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table(TABLE_NAME)

def send_dynamic_email(recipient_email, battery_id, rul, grade):
    """Sends a professional HTML Battery Health Report to any user-specified email"""
    if not SENDER_EMAIL or not SENDER_PASSWORD or not recipient_email:
        return
    
    msg = MIMEMultipart()
    msg['From'] = f"EV Battery Health Cloud <{SENDER_EMAIL}>"
    msg['To'] = recipient_email
    
    badge_color = "#10b981" if "A (" in grade else ("#f59e0b" if "B (" in grade else "#ef4444")
    
    msg['Subject'] = f"⚡ EV Battery Health Report: {battery_id} ({grade.split(' ')[0]})"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f3f4f6; padding: 20px;">
        <div style="max-width: 550px; background: white; border-radius: 10px; padding: 25px; margin: auto; border: 1px solid #e5e7eb;">
            <h2 style="color: #1f2937; margin-top: 0;">🔋 EV Battery Diagnostic Certificate</h2>
            <p style="color: #4b5563;">Here is the real-time health analysis for vehicle: <b>{battery_id}</b></p>
            <div style="background-color: #f9fafb; border-left: 5px solid {badge_color}; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h3 style="margin: 0; color: {badge_color};">{grade}</h3>
                <h1 style="margin: 10px 0; color: #111827;">~{rul:.1f} <span style="font-size: 16px; color: #6b7280;">cycles remaining</span></h1>
            </div>
            <table style="width: 100%; font-size: 14px; color: #374151; border-collapse: collapse;">
                <tr><td style="padding: 6px 0;"><b>Report Generated:</b></td><td>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
                <tr><td style="padding: 6px 0;"><b>Cloud Provider:</b></td><td>AWS Lambda Serverless ML</td></tr>
            </table>
            <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="font-size: 12px; color: #9ca3af; text-align: center;">Powered by NASA PCoE Battery Degradation Benchmark & AWS Cloud</p>
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
        
        # ML Inference
        predicted_rul = float(score(x))
        
        if predicted_rul > 600:
            grade = "Grade A (Healthy - >80% SOH)"
        elif predicted_rul > 200:
            grade = "Grade B (Moderate - 60-80% SOH)"
        else:
            grade = "Grade C (Degraded - Replace/Recycle)"
            
        timestamp_str = datetime.now(timezone.utc).isoformat()
        
        # DynamoDB Log
        try:
            table.put_item(
                Item={
                    "battery_id": battery_id,
                    "timestamp": timestamp_str,
                    "predicted_rul": Decimal(str(round(predicted_rul, 1))),
                    "grade": grade,
                    "recipient_email": user_email
                }
            )
        except Exception as db_err:
            print(f"DynamoDB Error: {db_err}")
            
        # Send dynamic email directly to user's entered email
        if user_email:
            send_dynamic_email(user_email, battery_id, predicted_rul, grade)

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