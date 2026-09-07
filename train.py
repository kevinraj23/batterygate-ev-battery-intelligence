# train.py
import pandas as pd
import numpy as np
import joblib
import sys
import io
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_FILE = "Battery_RUL.csv"

# Pure physical features (no Cycle_Index leakage!)
# Using the 6 core electrochemical features from HNEI dataset
FEATURES = [
    "Discharge Time (s)", 
    "Max. Voltage Dischar. (V)",
    "Min. Voltage Charg. (V)", 
    "Time at 4.15V (s)",
    "Time constant current (s)", 
    "Charging time (s)"
]
TARGET = "RUL"

# 1. Load Data
print(f"[*] Loading '{DATA_FILE}'...")
df = pd.read_csv(DATA_FILE)

# Data validation
print("=" * 55)
print(f"[DATA] DATASET SUMMARY (HNEI NMC-LCO 18650 Cells):")
print(f"   Rows       : {len(df):,}")
print(f"   Columns    : {list(df.columns)}")
print(f"   RUL range  : {df[TARGET].min():.0f} - {df[TARGET].max():.0f} cycles")
print(f"   Features   : {len(FEATURES)}")
for f in FEATURES:
    print(f"     {f:35s} : {df[f].min():.2f} - {df[f].max():.2f}")
print("=" * 55)

X = df[FEATURES]
y = df[TARGET]

# 2. Train/Test Split (80% Train, 20% Unseen Test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"\n[SPLIT] {len(X_train):,} train / {len(X_test):,} test samples")

# 3. Train Random Forest Model (optimized for serverless Lambda execution)
print("[TRAIN] Training Random Forest Regressor on real HNEI battery data...")
model = RandomForestRegressor(n_estimators=30, max_depth=8, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# 4. Evaluate
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)

print("\n" + "=" * 55)
print(f"[RESULT] BATTERY HEALTH MODEL - REAL DATA RESULTS:")
print(f"   MAE  : {mae:.2f} cycles")
print(f"   R2   : {r2:.4f}")
print(f"   RUL range in test set: {y_test.min():.0f} - {y_test.max():.0f}")
print("=" * 55)

# 5. Feature Importance
print("\n[FEATURES] Feature Importance:")
for fname, imp in sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1]):
    bar = "#" * int(imp * 50)
    print(f"   {fname:35s} : {imp:.4f}  {bar}")

# 6. Save Model
joblib.dump(model, "model.pkl")
print(f"\n[SAVED] Trained model saved to 'model.pkl'.")

# 7. Transpile model to pure Python for AWS Lambda (no sklearn dependency)
print("\n[TRANSPILE] Generating model_code.py (pure Python)...")

def transpile_forest(model):
    """Transpile entire Random Forest to pure Python score() function."""
    all_lines = ["def score(input):"]
    
    for i, tree in enumerate(model.estimators_):
        tree_ = tree.tree_
        feature_indices = tree_.feature
        thresholds = tree_.threshold
        values = tree_.value
        
        var_name = f"var{i}"
        
        def recurse(node, depth, var_name=var_name):
            prefix = "    " * (depth + 1)
            if feature_indices[node] != -2:
                all_lines.append(f"{prefix}if input[{feature_indices[node]}] <= {thresholds[node]}:")
                recurse(tree_.children_left[node], depth + 1, var_name)
                all_lines.append(f"{prefix}else:")
                recurse(tree_.children_right[node], depth + 1, var_name)
            else:
                val = float(values[node].flatten()[0])
                all_lines.append(f"{prefix}{var_name} = {val}")
        
        recurse(0, 0)
    
    # Average all trees
    tree_vars = [f"var{i}" for i in range(len(model.estimators_))]
    all_lines.append(f"    return ({' + '.join(tree_vars)}) / {len(tree_vars)}")
    
    return "\n".join(all_lines)

code = transpile_forest(model)
with open("model_code.py", "w") as f:
    f.write(code + "\n")

print(f"[TRANSPILE] Written model_code.py ({len(code):,} bytes)")

# Verify transpiled model matches sklearn
import importlib
import model_code
importlib.reload(model_code)
from model_code import score as transpiled_score

test_row = X_test.iloc[0].tolist()
sklearn_pred = model.predict([test_row])[0]
transpiled_pred = transpiled_score(test_row)
print(f"   sklearn prediction    : {sklearn_pred:.2f}")
print(f"   transpiled prediction : {transpiled_pred:.2f}")
diff = abs(sklearn_pred - transpiled_pred)
print(f"   match: {'YES' if diff < 0.01 else 'NO'} (diff={diff:.4f})")

print("\n[DONE] model.pkl + model_code.py are ready for deployment.")