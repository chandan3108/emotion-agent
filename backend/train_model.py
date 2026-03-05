"""Offline training script for a simple emotion model.

This does NOT run in the web server. You run it manually from the
backend directory, after you've collected enough data in
`realtime_log.csv` or `realtime_labeled.csv`.

Steps:
  1. Let the app run for a while so logs fill up.
  2. Use the /realtime/feedback endpoint (or edit the CSV) to add a
     `true_emotion` column with labels you consider ground truth.
  3. Run:  `python train_model.py` (or your preferred Python executable).
  4. It will train a small RandomForest model and save it to
     `models/emotion_model.joblib`.
  5. The FastAPI app can then load that file via ml_model.py.
"""

import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(__file__)
LOG_PATH = os.path.join(BASE_DIR, "realtime_log.csv")
LABELED_LOG_PATH = os.path.join(BASE_DIR, "realtime_labeled.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "emotion_model.joblib")

os.makedirs(MODEL_DIR, exist_ok=True)


def main() -> None:
    # Prefer explicitly labeled feedback data if available.
    source_path = LABELED_LOG_PATH if os.path.exists(LABELED_LOG_PATH) else LOG_PATH

    if not os.path.exists(source_path):
        raise SystemExit(
            f"No log file found at {source_path}. Collect some data and/or feedback first."
        )

    df = pd.read_csv(source_path)
    print(f"Loaded {len(df)} rows from {source_path}")

    # Use all numeric feature columns as inputs, excluding prediction cols and timestamp.
    drop_cols = ["timestamp"] + [c for c in df.columns if c.startswith("pred_")]
    feature_cols = [c for c in df.columns if c not in drop_cols and df[c].dtype != "object"]

    if not feature_cols:
        raise SystemExit("No numeric feature columns found to train on.")

    X = df[feature_cols].fillna(0.0).values

    # If you added a true_emotion column, train a classifier; otherwise
    # just show you how to proceed.
    if "true_emotion" not in df.columns:
        print(
            "No `true_emotion` column found in log. Use the /realtime/feedback "
            "endpoint or add labels to some rows and rerun this script to actually train."
        )
        print(f"Numeric feature columns: {feature_cols}")
        return

    y_cls = df["true_emotion"].astype(str).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_cls, test_size=0.2, random_state=42, stratify=y_cls
    )

    # Make the model a bit more sensitive to sadness (and low-mood states)
    # without breaking other labels. We start with per-class weight 1.0,
    # then gently upweight some classes if they are present.
    unique_labels = sorted(set(y_cls))
    class_weight = {label: 1.0 for label in unique_labels}
    for label, weight in {
        "sad": 2.0,        # encourage detecting sadness
        "calm": 1.3,       # distinguish calm from neutral/excited
        "neutral": 1.3,    # avoid everything collapsing to neutral
    }.items():
        if label in class_weight:
            class_weight[label] = weight

    clf = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight=class_weight,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("\nClassification report (emotion):")
    print(classification_report(y_test, y_pred))

    joblib.dump(
        {
            "feature_cols": feature_cols,
            "classifier": clf,
        },
        MODEL_PATH,
    )
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
