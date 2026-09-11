# ⚡ BatteryGate — EV Battery Health & Lifespan Intelligence

> **Think of BatteryGate like the "Battery Health %" feature on an iPhone — but built for Electric Vehicles.**

BatteryGate is a serverless AI platform that tells you **exactly how healthy an EV battery is** and **how many charging cycles it has left** before it needs replacement.

---

## 🧐 What Problem Does This Solve?

The battery is the most expensive part of an electric car (up to **50% of the vehicle's total cost**).

* **The odometer lies:** A car with only 20,000 km that was frequently fast-charged in extreme heat can have a worse battery than one driven 60,000 km with gentle overnight charging.
* **Buyers have no way to verify health:** When buying a used EV, there is no simple way to check if the battery pack will fail in 6 months.
* **BatteryGate solves this:** By analyzing a single charging/discharging session, our AI predicts the battery's Remaining Useful Life with **98.8% accuracy**.

---

## 🚀 How It Works (In 3 Steps)

```text
  [ 1. Input Telemetry ]       ──► [ 2. AI Brain (AWS Lambda) ] ──► [ 3. Instant Report ]
  Enter 6 charge/drive numbers      Predicts remaining cycles        • Speedometer gauge
  (discharge time, voltages)        in under 0.05 seconds            • Emailed Certificate
```

1. **Input Telemetry:** Enter 6 observable numbers from a charging session (how long it took to charge, how long it drove, and voltage levels).
2. **Instant AI Prediction:** A lightweight model running on AWS Lambda checks the battery's degradation symptoms against **15,064 real lab test cycles**.
3. **Automated Certification:** The system assigns a clear Letter Grade (**A, B, or C**), logs the report to **DynamoDB**, and **emails an official Diagnostic Certificate** to the user.

---

## 🏷️ The Health Grading System

| Grade | Balance Life | Health % | What It Means for You |
| :---: | :---: | :---: | :--- |
| 🟢 **Grade A** | **> 600 cycles** | **80% – 100%** | **Prime Condition:** Safe for DC fast charging and highway road trips. |
| 🟡 **Grade B** | **200 – 600 cycles** | **60% – 80%** | **Moderate Aging:** Noticeable range reduction. Cell balancing recommended at next service. |
| 🔴 **Grade C** | **< 200 cycles** | **< 60%** | **Critical (End of Life):** High risk of sudden shutdown. Immediate replacement alert sent. |

---

## 🔬 Real Data, Real Physics (No Cheating)

Most battery projects "cheat" by using the odometer or cycle counter as an input. But in the real world, you don't always know or trust the car's history.

BatteryGate uses **only 6 real physical measurements**:
* **Discharge Duration (s):** How long the battery lasted under load.
* **Max & Min Voltages (V):** Peak and lowest voltage levels during cycling.
* **Time at 4.15V (s):** How long the battery can hold peak voltage.
* **Constant Current Duration (s):** Time spent absorbing full charge speed.
* **Total Charging Time (s):** Total time needed for a full charge.

**Trained on real data:** Hawaii Natural Energy Institute (HNEI) experimental dataset of 15,064 lithium-ion 18650 cell cycles.

---

## ⚡ Technical Highlights

* **Sub-50ms Speed:** Pure-Python model transpilation (`model_code.py`) runs without heavy libraries (`scikit-learn` or `numpy` not needed at runtime).
* **BatterySentry Copilot:** Real-time thermal runaway threat modeling ($0\text{--}100\%$) and adaptive BMS charging prescription powered by live climate data (Open-Meteo) and Google Gemini AI reasoning.
* **$0 Idle Cost:** Powered entirely by AWS Lambda serverless architecture.
* **Live Storage & Email:** AWS DynamoDB records all scans; automated HTML certificates sent via SMTP.

---

## 💻 Quickstart (Run Locally)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Web Portal
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`. Click on any vehicle preset (**Tata Nexon EV**, **Ather 450X**, or **Ola S1**) and hit **RUN AI DIAGNOSIS**!

### 3. Test the Live Cloud API
```bash
python client.py
```
Sends real test payloads to your live AWS Lambda endpoint and prints the diagnosis.

---

## 📂 Project Structure

| File | What It Does |
| :--- | :--- |
| `app.py` | Full-screen Streamlit application wrapper. |
| `index.html` | Interactive diagnostic portal with live SVG degradation curves & gauges. |
| `train.py` | Trains the Random Forest on real HNEI data & generates `model_code.py`. |
| `model_code.py` | Lightweight pure-Python decision forest (runs anywhere with zero dependencies). |
| `lambda_function.py` | AWS Lambda cloud handler with DynamoDB logging and email dispatch. |
| `client.py` | Python test script to ping the live AWS Lambda Function URL. |
| `Battery_RUL.csv` | Real experimental HNEI battery degradation dataset (15,064 rows). |
