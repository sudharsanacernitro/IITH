# -*- coding: utf-8 -*-
"""
Modularized crop classification pipeline using Random Forest and Balanced Random Forest
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, classification_report
from sklearn.ensemble import RandomForestClassifier
from imblearn.ensemble import BalancedRandomForestClassifier


# ------------------ Data Utilities ------------------ #
def balance_class_samples(input_file_path, sample_size):
    df = pd.read_csv(input_file_path)
    print('Original Class Distribution:', df['Class'].value_counts())

    balanced_classes = []
    for class_label in df['Class'].unique():
        class_subset = df[df['Class'] == class_label]
        if len(class_subset) >= sample_size:
            balanced_classes.append(class_subset.sample(n=sample_size, random_state=42))
        else:
            print(f"Class {class_label} has only {len(class_subset)} samples. Using all.")
            balanced_classes.append(class_subset)

    df_balanced = pd.concat(balanced_classes).sample(frac=1, random_state=42).reset_index(drop=True)
    print('Balanced Class Distribution:', df_balanced['Class'].value_counts())
    return df_balanced


# ------------------ Split Utility ------------------ #
def custom_train_test_split(df, test_size):
    X = df.drop(['Class'], axis=1)
    y = df['Class']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    print('Train shape:', X_train.shape, 'Test shape:', X_test.shape)
    print(y_train.value_counts(), y_test.value_counts())
    return X_train, X_test, y_train, y_test


# ------------------ Model Utilities ------------------ #
def plot_feature_importance(model, columns, save_path):
    feature_scores = pd.Series(model.feature_importances_, index=columns).sort_values(ascending=False)
    plt.figure(figsize=(8, 6))
    sns.barplot(x=feature_scores, y=feature_scores.index)
    plt.xlabel('Feature Importance Score')
    plt.ylabel('Features')
    plt.title("Feature Importance")
    plt.tight_layout()
    plt.savefig(save_path)


def custom_random_forest_classifier(X_train, X_test, y_train, y_test, n_estimators, save_path):
    rfc = RandomForestClassifier(n_estimators=n_estimators, random_state=0)
    rfc.fit(X_train, y_train)
    y_pred = rfc.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    model_filename = f"{save_path}RF_crops3inc_multiclass_{accuracy:.4f}.joblib"
    joblib.dump(rfc, model_filename)
    
    plot_feature_importance(rfc, X_train.columns, f"{save_path}RF_crops3inc_multiclass_{accuracy:.4f}_FeatureImportance.png")
    return model_filename, accuracy, y_pred


def custom_balanced_random_forest_classifier(X_train, X_test, y_train, y_test, n_estimators, save_path):
    brfc = BalancedRandomForestClassifier(
        n_estimators=n_estimators,
        sampling_strategy="all",
        replacement=True,
        random_state=0,
        bootstrap=False
    )
    brfc.fit(X_train, y_train)
    y_pred = brfc.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    model_filename = f"{save_path}BRF_crops3inc_multiclass_{accuracy:.4f}.joblib"
    joblib.dump(brfc, model_filename)
    
    plot_feature_importance(brfc, X_train.columns, f"{save_path}BRF_crops3inc_multiclass_{accuracy:.4f}_FeatureImportance.png")
    return model_filename, accuracy, y_pred


# ------------------ Evaluation Utilities ------------------ #
def evaluation_metrics(labels, y_test, y_pred, save_path, model_type, accuracy):
    cm_path = f"{save_path}{model_type}_crops3inc_multiclass_{accuracy:.4f}_confusion_matrix.png"
    report_path = f"{save_path}{model_type}_crops3inc_multiclass_{accuracy:.4f}_classif_report.txt"

    cm = confusion_matrix(y_test, y_pred)
    cmd = ConfusionMatrixDisplay(cm, display_labels=labels)
    cmd.plot()
    plt.title("Confusion Matrix")
    plt.savefig(cm_path)

    report = classification_report(y_test, y_pred)
    print(report)
    with open(report_path, 'w') as f:
        f.write(report)

    return cm_path, report_path


# ------------------ Main Runner ------------------ #
def modelCreation_PipeLine(project_name, sample_size, test_size, n_trees):
    input_dir = rf"Crop_mapping_{project_name}"
    save_path = rf"{input_dir}/metrics/"
    input_file_path = rf"{input_dir}/timeseries/crops3inc_multiclass_S1S2_onlytimeseries_v01.csv"
    label_file_path = f"{input_dir}/NDVI_timeseries_{project_name}.csv"

    df_labels = pd.read_csv(label_file_path)
    if 'crpname_eg' not in df_labels.columns:
        raise KeyError(f"The file {label_file_path} does not contain the 'crpname_eg' column.")
    labels = df_labels['crpname_eg'].unique().tolist()
    print("Extracted labels:", labels)

    balanced_df = balance_class_samples(input_file_path, sample_size)
    X_train, X_test, y_train, y_test = custom_train_test_split(balanced_df, test_size)

    model_rfc, acc_rfc, y_pred_rfc = custom_random_forest_classifier(X_train, X_test, y_train, y_test, n_trees, save_path)
    model_brfc, acc_brfc, y_pred_brfc = custom_balanced_random_forest_classifier(X_train, X_test, y_train, y_test, n_trees, save_path)

    evaluation_metrics(labels, y_test, y_pred_rfc, save_path, "RF", acc_rfc)
    evaluation_metrics(labels, y_test, y_pred_brfc, save_path, "BRF", acc_brfc)


# ------------------ Entry Point ------------------ #
if __name__ == "__main__":
    modelCreation_PipeLine(
        project_name="ujjain",
        sample_size=400,
        test_size=0.33,
        n_trees=500
    )
