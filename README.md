# BatteryGate — Serverless EV Battery Health & RUL Prediction

An end-to-end serverless battery intelligence platform that estimates **Remaining Useful Life (RUL)** and **State of Health (SOH)** of lithium-ion batteries using real experimental battery degradation data from the **Hawaii Natural Energy Institute (HNEI)** and zero-dependency **AWS Lambda ML inference**.

---

## ⚡ Live Architecture

```text
  [ Battery Telemetry / Web App ]
                 │
                 ▼ (HTTPS POST JSON)
  [ AWS Lambda Serverless ML Engine ] ──► [ Amazon DynamoDB (Report Store) ]
                 │
                 ▼
  [ Dynamic Email Certificate Dispatch ] ──► [ User Inbox ]
```

---

## 🔬 Dataset & Physics

The model is trained on the real **Hawaii Natural Energy Institute (HNEI)** dataset consisting of **15,064 experimental charge-discharge cycles** on commercial 18650 NMC-LCO lithium-ion cells operated under constant 1C cycling conditions.

### Leakage-Free Physical Features (6 Inputs)
To ensure true predictive capability on in-service batteries without label leakage (such as knowing the cycle counter), the model relies strictly on observable electrochemical and operational telemetry:

| Feature | Unit | Physical Significance |
| :--- | :--- | :--- |
| **Discharge Time (s)** | seconds | Cell usable capacity indicator during constant current discharge |
| **Max. Voltage Dischar. (V)** | Volts | Peak voltage observed during discharge onset |
| **Min. Voltage Charg. (V)** | Volts | Lowest voltage at the start of charge cycle |
| **Time at 4.15V (s)** | seconds | Constant-voltage (CV) saturation phase duration |
| **Time constant current (s)** | seconds | Duration battery sustains constant current (CC) charging |
| **Charging time (s)** | seconds | Full charging duration |

**Target Variable:**
- **RUL (Remaining Useful Life):** Measured in cycles until battery reaches 80% capacity retention threshold (End of Life / EOL). Range: **0 – 1,133 cycles**.

---

## 📊 Model Performance

Trained using a **Random Forest Regressor** (100 estimators, max depth 12) evaluated on an unseen 20% test split (3,013 cycles):

- **$R^2$ Score:** `0.9930` (99.30% variance explained)
- **Mean Absolute Error (MAE):** `14.11` cycles
- **Inference Latency:** `< 0.05` seconds (pure Python transpilation)

### Feature Importance

```text
Discharge Time (s)                  : 88.49%  ############################################
Time constant current (s)           :  5.59%  ##
Time at 4.15V (s)                   :  3.06%  #
Max. Voltage Dischar. (V)           :  1.68%  
Min. Voltage Charg. (V)             :  0.65%  
Charging time (s)                   :  0.54%  
```

---

## 🛡️ Health Grading Matrix

| Grade | RUL Range | Est. SOH | Recommendation |
| :--- | :--- | :--- | :--- |
| **Grade A** | `> 600 cycles` | `80% – 100%` | Healthy condition. Suitable for DC fast-charging & highway demand. |
| **Grade B** | `200 – 600 cycles` | `60% – 80%` | Moderate degradation. Recommend cell balancing at service. |
| **Grade C** | `≤ 200 cycles` | `< 60%` | Critical degradation. Automated alert emailed; replacement advised. |

---

## 🚀 Repository Structure

- `train.py`: Data loader, 80/20 train/test evaluation, and automated Python transpiler.
- `Battery_RUL.csv`: Real HNEI 18650 cycling dataset (15,064 records).
- `model.pkl`: Serialized scikit-learn model artifact.
- `model_code.py`: Zero-dependency, transpiled pure-Python decision forest for sub-50ms execution on AWS Lambda.
- `lambda_function.py`: AWS Lambda handler with DynamoDB logging and dynamic SMTP certificate dispatch.
- `client.py`: Python CLI client for testing live AWS endpoints with realistic payloads.
- `index.html`: High-fidelity telemetry portal with interactive SVG degradation charts, presets, and diagnostic dashboard.
- `app.py`: Streamlit wrapper for embedding the portal in full-screen mode.

---

## 💻 Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train model on real data & auto-generate model_code.py
python train.py

# 3. Test client against AWS Lambda
python client.py

# 4. Launch web application
streamlit run app.py
```
