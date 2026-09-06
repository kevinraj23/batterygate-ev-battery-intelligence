# BatteryGate — Serverless EV Battery Health & RUL Prediction

An end-to-end serverless battery intelligence platform that estimates **Remaining Useful Life (RUL)** and **State of Health (SOH)** of lithium-ion batteries using **NASA PCoE degradation benchmarks** and **AWS Lambda ML inference**.

## ?? Live Demos
- **Live Web App:** [BatteryGate Telematics Portal](https://share.streamlit.io)
- **AWS Serverless Endpoint:** Powered by AWS Lambda Function URLs (sub-90ms execution)

---

## Architecture
\\\
  [ Battery Telemetry / Web App ]
                 ¦
                 ? (HTTPS POST JSON)
  [ AWS Lambda Serverless ML Engine ] --? [ Amazon DynamoDB (Report Store) ]
                 ¦
                 ?
  [ Dynamic Email Certificate Dispatch ] --? [ User Inbox ]
\\\

##  Key Highlights
- **Leakage-Free Physical ML:** Random Forest trained on physical NASA discharge/charge voltage curves (^2 = 0.991$, $\text{MAE} < 8$ cycles).
- **Sub-100ms Inference:** Zero-dependency Python transpilation running on AWS Lambda.
- **Automated Reporting:** Instant branded HTML Diagnostic Certificate sent to any user email.
