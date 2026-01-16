import json
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


def load_parquet_folder(folder_path: str) -> pd.DataFrame:
    files = sorted([f for f in os.listdir(folder_path) if f.endswith(".parquet")])
    if not files:
        raise FileNotFoundError(f"No parquet files found in: {folder_path}")

    dfs = []
    for file_name in files:
        full_path = os.path.join(folder_path, file_name)
        print(f"Loading {file_name} ...")
        dfs.append(pd.read_parquet(full_path))

    return pd.concat(dfs, ignore_index=True)


def prepare_features(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, LabelEncoder]:
    if "Label" not in data.columns:
        raise KeyError("Expected a 'Label' column in training data.")

    drop_cols = [
        "Flow ID",
        "Source IP",
        "Src IP",
        "Dest IP",
        "Destination IP",
        "Timestamp",
        "External IP",
    ]
    cols_to_drop = [col for col in drop_cols if col in data.columns]
    data = data.drop(columns=cols_to_drop)

    # Keep original labels for Isolation Forest anomaly mapping.
    y_text = data["Label"].astype(str)
    X = data.drop(columns=["Label"]).copy()

    # Force numeric features for sklearn models.
    X = X.apply(pd.to_numeric, errors="coerce")
    X.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Drop mostly-empty columns and impute remaining missing values with median.
    missing_ratio = X.isna().mean()
    keep_cols = missing_ratio[missing_ratio < 0.95].index.tolist()
    X = X[keep_cols]
    X = X.fillna(X.median(numeric_only=True))

    # Remove constant columns to reduce noise.
    nunique = X.nunique(dropna=False)
    variable_cols = nunique[nunique > 1].index.tolist()
    X = X[variable_cols]

    # Align rows with non-empty labels.
    valid_rows = y_text.notna() & (y_text.str.len() > 0)
    X = X.loc[valid_rows]
    y_text = y_text.loc[valid_rows]

    le = LabelEncoder()
    y = pd.Series(le.fit_transform(y_text), index=X.index)

    if len(X) == 0:
        raise ValueError("No valid rows remain after preprocessing.")

    print(f"Prepared feature matrix shape: {X.shape}")
    print(f"Classes: {list(le.classes_)}")
    return X, y_text, le


def main() -> None:
    folder = os.getenv("DATA_PATH", "data")
    model_path = os.getenv("MODEL_PATH", ".")
    os.makedirs(model_path, exist_ok=True)

    print(f"Using DATA_PATH={folder}")
    print(f"Using MODEL_PATH={model_path}")

    data = load_parquet_folder(folder)
    print(f"Initial shape: {data.shape}")

    X, y_text, le = prepare_features(data)
    y_encoded = pd.Series(le.transform(y_text), index=X.index)

    # 1) Random Forest (multiclass supervised)
    print("\n--- Training Random Forest ---")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded,
    )

    rf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    rf_accuracy = accuracy_score(y_test, y_pred)
    print(f"Random Forest Accuracy: {rf_accuracy * 100:.2f}%")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    with open(os.path.join(model_path, "random_forest_model.pkl"), "wb") as f:
        pickle.dump(rf, f)
    # Compatibility with services that use this filename.
    with open(os.path.join(model_path, "random_forest.pkl"), "wb") as f:
        pickle.dump(rf, f)
    print("Random Forest model saved")

    # 2) Isolation Forest (binary anomaly detection)
    print("\n--- Training Isolation Forest ---")
    y_binary = (~y_text.str.lower().str.contains("benign", na=False)).astype(int)

    X_train_iso, X_test_iso, y_train_iso, y_test_iso = train_test_split(
        X,
        y_binary,
        test_size=0.2,
        random_state=42,
        stratify=y_binary,
    )

    scaler = StandardScaler()
    benign_train = X_train_iso[y_train_iso == 0]
    if len(benign_train) == 0:
        raise ValueError("No benign samples found for Isolation Forest training.")

    X_train_scaled = scaler.fit_transform(benign_train)
    X_test_scaled = scaler.transform(X_test_iso)

    contamination = float(np.clip(y_train_iso.mean(), 0.001, 0.49))
    iso = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    iso.fit(X_train_scaled)

    scores = iso.decision_function(X_test_scaled)
    thresholds = np.linspace(scores.min(), scores.max(), 200)
    best_acc = 0.0
    best_thresh = 0.0
    best_pred = None

    for thresh in thresholds:
        y_pred_iso = (scores < thresh).astype(int)
        acc = accuracy_score(y_test_iso, y_pred_iso)
        if acc > best_acc:
            best_acc = acc
            best_thresh = float(thresh)
            best_pred = y_pred_iso

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test_iso,
        best_pred,
        average="binary",
        zero_division=0,
    )

    print(f"Best Anomaly Threshold: {best_thresh:.6f}")
    print(f"Isolation Forest Accuracy: {best_acc * 100:.2f}%")
    print(
        "Isolation Forest Precision/Recall/F1: "
        f"{precision:.4f}/{recall:.4f}/{f1:.4f}"
    )

    model_data = {
        "isolation_forest": iso,
        "scaler": scaler,
        "label_encoder": le,
        "best_threshold": best_thresh,
    }
    with open(os.path.join(model_path, "isolation_forest_model.pkl"), "wb") as f:
        pickle.dump(model_data, f)
    # Compatibility with services that use this filename.
    with open(os.path.join(model_path, "isolation_forest.pkl"), "wb") as f:
        pickle.dump(model_data, f)
    print("Isolation Forest model saved")

    # 3) Feature importance visualization
    importances = rf.feature_importances_
    top_n = min(10, len(importances))
    indices = np.argsort(importances)[-top_n:]

    plt.figure(figsize=(10, 6))
    plt.title("Top Predictors of Cyber Threats")
    plt.barh(range(len(indices)), importances[indices], color="crimson", align="center")
    plt.yticks(range(len(indices)), [X.columns[i] for i in indices])
    plt.xlabel("Importance Score")
    plt.tight_layout()
    plt.savefig(os.path.join(model_path, "feature_importance.png"))

    metrics_summary = {
        "random_forest_accuracy": float(rf_accuracy),
        "isolation_forest_accuracy": float(best_acc),
        "isolation_forest_precision": float(precision),
        "isolation_forest_recall": float(recall),
        "isolation_forest_f1": float(f1),
        "isolation_forest_best_threshold": float(best_thresh),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "features": int(X.shape[1]),
    }
    with open(os.path.join(model_path, "model_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    print("\n--- Model Saving Summary ---")
    print("✓ Random Forest model saved")
    print("✓ Isolation Forest model saved")
    print("✓ Feature importance plot saved")
    print("✓ Metrics summary saved to model_metrics.json")


if __name__ == "__main__":
    main()