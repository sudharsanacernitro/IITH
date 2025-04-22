# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 11:55:48 2024

@author: iith
"""

# libraries
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt # data visualization
import seaborn as sns # statistical data visualization

from sklearn.model_selection import train_test_split, RandomizedSearchCV, GridSearchCV
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, ConfusionMatrixDisplay, classification_report
import joblib

from sklearn.ensemble import RandomForestClassifier
from imblearn.ensemble import BalancedRandomForestClassifier



def balance_class_samples(input_df, sample_size):
    df = pd.read_csv(input_df)
    print('Classes and Counts', df['Class'].value_counts())

    # Initialize an empty list to store balanced class samples
    balanced_classes = []

    # Iterate through each unique class
    for class_label in df['Class'].unique():
        class_subset = df[df['Class'] == class_label]
        if len(class_subset) >= sample_size:
            # Sample if there are enough rows
            balanced_classes.append(class_subset.sample(n=sample_size, random_state=42))
        else:
            # Use all available rows if not enough samples
            print(f"Class {class_label} has fewer samples ({len(class_subset)}) than the requested sample size ({sample_size}). Using all available samples.")
            balanced_classes.append(class_subset)

    # Concatenate all balanced class samples
    df_balanced = pd.concat(balanced_classes)

    # Shuffle the resulting DataFrame to mix classes
    df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
    print('Balanced Classes and Counts', df_balanced['Class'].value_counts())

    return df_balanced


def custom_train_test_split(df, test_size):

  # declare features and target variable
  X = df.drop(['Class'], axis=1)
  y = df['Class']


  # split data into training and testing sets
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size, random_state = 42)
  print('Train shape:', X_train.shape, 'Test shape:', X_test.shape)
  print(y_train.value_counts(), y_test.value_counts())

  return X_train, X_test, y_train, y_test


def custom_random_forest_classifier(X_train, X_test, y_train, y_test, n_estimators, save_path):

  # instantiate the classifier with specified n_estimators
  rfc = RandomForestClassifier(
        n_estimators=n_trees, 
        random_state=0)

  # fit the model to the training set
  rfc.fit(X_train, y_train)

  # Predict on the test set results
  y_pred = rfc.predict(X_test)

  # Check accuracy score
  accuracy = accuracy_score(y_test, y_pred)
  print(f'Model accuracy score with {n_estimators} decision-trees : {accuracy:.4f}')

  # save the model
  model_filename = f"{save_path}RF_crops3inc_multiclass_{accuracy:.4f}.joblib"
  joblib.dump(rfc, model_filename)
  
  
  # Generate feature scores 
  fe_imp_save_path = f"{save_path}RF_crops3inc_multiclass_{accuracy:.4f}_FeatureImportance.png"
  feature_scores = pd.Series(rfc.feature_importances_, index=X_train.columns).sort_values(ascending=False)
  plt.figure(figsize=(8, 6))
  sns.barplot(x=feature_scores, y=feature_scores.index)
  plt.xlabel('Feature Importance Score')
  plt.ylabel('Features')
  plt.title("Visualizing Important Features RF")
  plt.tight_layout()
  plt.savefig(fe_imp_save_path)
    

  return model_filename, accuracy, y_pred


def custom_balanced_random_forest_classifier(X_train, X_test, y_train, y_test, n_estimators, save_path):

    # Instantiate the BalancedRandomForestClassifier
    brfc = BalancedRandomForestClassifier(
           n_estimators=n_estimators,
           sampling_strategy="all",
           replacement=True,
           random_state=0,
           bootstrap=False)

    # Fit the model to the training set
    brfc.fit(X_train, y_train)

    # Predict on the test set
    y_pred = brfc.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f'Model accuracy score with {n_estimators} decision-trees : {accuracy:.4f}')

    # Save the model with accuracy in the filename
    model_filename = f"{save_path}BRF_crops3inc_multiclass_{accuracy:.4f}.joblib"
    joblib.dump(brfc, model_filename)
    
    # Generate feature scores 
    fe_imp_save_path = f"{save_path}BRF_crops3inc_multiclass_{accuracy:.4f}_FeatureImportance.png"
    feature_scores = pd.Series(brfc.feature_importances_, index=X_train.columns).sort_values(ascending=False)
    plt.figure(figsize=(8, 6))
    sns.barplot(x=feature_scores, y=feature_scores.index)
    plt.xlabel('Feature Importance Score')
    plt.ylabel('Features')
    plt.title("Visualizing Important Features BRF")
    plt.tight_layout()
    plt.savefig(fe_imp_save_path)

    return model_filename, accuracy, y_pred


def evaluation_metrics(labels, y_test, y_pred, save_path, model_type, accuracy):
    
    cm_fig_path = f"{save_path}{model_type}_crops3inc_multiclass_{accuracy:.4f}_confusion_matrix.png"
    report_path = f"{save_path}{model_type}_crops3inc_multiclass_{accuracy:.4f}_classif_report.txt"

      
    #generate and display confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    cmd = ConfusionMatrixDisplay(cm, display_labels=labels)
    cmd.plot()
    plt.title("Confusion Matrix")
    plt.savefig(cm_fig_path) 
    #plt.close()  # Close to free up memory
  
    # print classification report
    classif_report = classification_report(y_test, y_pred)
    print(classif_report)    
    with open(report_path, 'w') as f:
      f.write(classif_report)
  
    return cm_fig_path, report_path




# Declare project name
project_name = "ujjain"

# File paths and parameters
input_dir = rf"Crop_mapping_{project_name}"
save_path = rf"{input_dir}/metrics/"  # Save path for all outputs

sample_size = 400
test_size = 0.33
n_trees = 500  # Number of trees for both classifiers

# Dynamically retrieve labels from one input CSV file
label_file_path = f"{input_dir}/NDVI_timeseries_{project_name}.csv"
df = pd.read_csv(label_file_path)
if 'crpname_eg' in df.columns:
    labels = df['crpname_eg'].unique().tolist()
else:
    raise KeyError(f"The file {label_file_path} does not contain the 'crpname_eg' column.")
print("Extracted labels:", labels)

# Step 1: Balance classes in the dataset
input_file_path = rf"{input_dir}/timeseries/crops3inc_multiclass_S1S2_onlytimeseries_v01.csv"
balanced_df = balance_class_samples(input_df=input_file_path, sample_size=sample_size)

# Step 2: Split the balanced dataset into train and test sets
X_train, X_test, y_train, y_test = custom_train_test_split(balanced_df, test_size=test_size)


# Step 3a: Train and save the Random Forest model
model_filename_rfc, accuracy_rfc, y_pred_rfc = custom_random_forest_classifier(
    X_train, X_test, y_train, y_test, n_estimators=n_trees, save_path=save_path)

# Step 3b: Train and save the Balanced Random Forest model
model_filename_brfc, accuracy_brfc, y_pred_brfc = custom_balanced_random_forest_classifier(
    X_train, X_test, y_train, y_test, n_estimators=n_trees, save_path=save_path)


# Step 4a: Evaluate the Random Forest model
evaluation_metrics(labels=labels, y_test=y_test, y_pred=y_pred_rfc, 
                   save_path=save_path, model_type= 'RF', accuracy = accuracy_rfc)

# Step 4b: Evaluate the Balanced Random Forest model
evaluation_metrics(labels=labels, y_test=y_test, y_pred=y_pred_brfc,save_path=save_path, 
                   model_type= 'BRF', accuracy = accuracy_brfc)