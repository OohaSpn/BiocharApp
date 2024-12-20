import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import joblib
import xgboost as xgb
from xgboost import XGBRegressor
from sklearn.model_selection import KFold, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV
from sklearn.metrics import make_scorer, mean_absolute_percentage_error, mean_squared_error
from sklearn.model_selection import cross_val_score, KFold, cross_validate, cross_val_predict

st.title('Evaluating Biochar')
st.info('''
    Biochar is a carbon-rich adsorbent material produced from the thermal decomposition of organic waste
    (such as crops, forestry residues, sewage sludge, algal biomass, and poultry manure) under controlled
    conditions. It is evaluated for its effectiveness in removing pharmaceutical pollutants from wastewater
    due to its high adsorption capacity, porous structure, and large surface area, which allow it to effectively
    capture and remove contaminants. This project focuses on comparing biochar's performance and optimizing
    conditions for its use in sustainable wastewater treatment.
''')


# Data Display
with st.expander('Data'):
    st.write('**Raw Data**')
    df = pd.read_csv("Updated_dataset.csv",  usecols=lambda column: column != 'Unnamed: 0')
    st.dataframe(df)

    st.write('**Numeric Columns**')
    numeric_columns = ['TemP', 'Time (min)', 'PS', 'BET', 'PV', 'C', 'N', 'H', 'O' , 'Qm (mg/g)']
    st.write(numeric_columns)

    st.write('**Categorical Columns**')
    cat_columns = ['raw_material', 'TP']
    st.write(cat_columns)

    st.write('**X**')
    X_raw = df.drop('Qm (mg/g)', axis=1)
    st.write(X_raw)

    st.write('**y**')
    y_raw = df['Qm (mg/g)']
    st.write(y_raw)

# Sidebar Inputs
with st.sidebar:
    st.header('Input feature For Biomass')
    raw_material = st.selectbox('Select Raw Material', df['raw_material'].unique())

    st.header('Input feature for Type of Pollutant')
    tp_value = st.selectbox('Select TP', df['TP'].unique())

# Filtered Data
filtered_df_biomass = df[df['raw_material'] == raw_material]
filtered_df_tp = df[df['TP'] == tp_value]

with st.expander("Filtered Data"):
    st.write(f"Filtered data for raw_material: **{raw_material}**")
    st.dataframe(filtered_df_biomass)

    st.write(f"Filtered data for TP: **{tp_value}**")
    st.dataframe(filtered_df_tp)

# Data Visualizations
with st.expander("Data Visualizations"):
    st.write("Boxplot for Each Column")

    # Create a figure with subplots
    fig, axes = plt.subplots(nrows=2, ncols=5, figsize=(15, 8))  # Adjust rows and columns as needed
    axes = axes.flatten()  # Flatten the 2D axes array to make indexing easier

    # Loop through the columns and plot each one in a separate subplot
    for i, column in enumerate(numeric_columns):
        df.boxplot(column=column, ax=axes[i])
        axes[i].set_title(f'Box plot for {column}')
        axes[i].set_xlabel('')

    plt.tight_layout()
    st.pyplot(fig)

    st.info('Boxplots help identify outliers and show how the data is distributed.')

    st.write('Distribution After Applying Log to Skewed Data')

    # Apply log transformation to skewed data
    df['Time (min)'] = np.log(df['Time (min)'] + 1)  # Add 1 to avoid log(0)
    df['BET'] = np.log(df['BET'] + 1)
    df['PS'] = np.log(df['PS'] + 1)

    # Create a figure with subplots for the log-transformed distributions
    fig, axes = plt.subplots(1, 3, figsize=(20, 5))
    sns.histplot(df['Time (min)'], kde=True, ax=axes[0])
    axes[0].set_title('Log-Transformed Distribution of Time (min)')
    sns.histplot(df['BET'], kde=True, ax=axes[1])
    axes[1].set_title('Log-Transformed Distribution of BET')
    sns.histplot(df['PS'], kde=True, ax=axes[2])
    axes[2].set_title('Log-Transformed Distribution of PS')

    plt.tight_layout()
    st.pyplot(fig)

    
    # Pearson Correlation
    st.write("Pearson Correlation Between Features")
    columns = ['TemP', 'Time (min)', 'PS', 'BET', 'PV', 'C', 'H', 'N', 'O', 'Qm (mg/g)']
    corr_matrix = df[columns].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5, cbar=True)
    st.pyplot(fig)
    st.info("There is a positive correlation between PV and BET with correlation value 0.67.")

   # Preprocessing the Data
    label_encoder = LabelEncoder()
    df['raw_material'] = label_encoder.fit_transform(df['raw_material'])
    
    X = df.drop(columns=['Qm (mg/g)', 'TP'])  # Drop target column
    y = df['Qm (mg/g)']  # Target column

# Model Training
with st.expander("Model Training"):
    st.write("Training an XGBoost Regressor model with GridSearchCV for hyperparameter tuning.")
    
    mape_scorer = make_scorer(mean_absolute_percentage_error, greater_is_better=False)
    
    # Set up K-Fold cross-validation and grid search parameters
    k_folds = KFold(n_splits=5)
    xgb_reg = XGBRegressor()  # Removed enable_categorical=True for compatibility
    
    param_xgb = {
        'n_estimators': [100, 200, 300, 400, 500],
        'learning_rate': [0.001, 0.01, 0.05, 0.1, 0.2],
        'max_depth': [3, 4, 5, 6, 7],
        'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
        'gamma': [0, 0.1, 0.2, 0.3, 0.4],
        'reg_alpha': [0, 0.1, 0.2, 0.3, 0.4],
        'reg_lambda': [0, 0.1, 0.2, 0.3, 0.4]
    }
    grid_search_xgb = GridSearchCV(xgb_reg, param_grid=param_xgb, scoring='r2', cv=k_folds, verbose=1, n_jobs=-1)
    grid_search_xgb.fit(X, y)  # X and y should be predefined datasets
    best_params_xgb = grid_search_xgb.best_params_
        
    st.write("Initial Parameters for Tuning:", param_xgb)
    st.write("Best Parameters:", best_params_xgb)
   

# K-Fold Cross-Validation with Best Model
with st.expander("K-Fold Cross-Validation Results"):
    st.write("Evaluating model performance with K-Fold cross-validation.")
    kfold_xgb_mape = cross_val_score(grid_search_xgb.best_estimator_, X, y.values.ravel(), cv = k_folds, scoring= mape_scorer) * -1
    kfold_xgb_rmse = np.sqrt(cross_val_score(grid_search_xgb.best_estimator_, X, y.values.ravel(), cv = k_folds, scoring= "neg_mean_squared_error")*-1)
    st.write(f"k-fold MAPE score: {np.mean(kfold_xgb_mape)}")
    st.write(f"k-fold RMSE score: {np.mean(kfold_xgb_rmse)}")

with st.expander("Want to predict"):
    # User inputs for each feature
    TemP = st.number_input('Enter Temperature (TemP)', value=0.0)
    Time_min = st.number_input('Enter Time (min)', value=0.0)
    PS = st.number_input('Enter Particle Size (PS)', value=0.0)
    BET = st.number_input('Enter BET Surface Area', value=0.0)
    PV = st.number_input('Enter Pore Volume (PV)', value=0.0)
    C = st.number_input('Enter Carbon content (C)', value=0.0)
    H = st.number_input('Enter Hydrogen content (H)', value=0.0)
    N = st.number_input('Enter Nitrogen content (N)', value=0.0)
    O = st.number_input('Enter Oxygen content (O)', value=0.0)
    Biomass_encoded = st.number_input('Enter Biomass', value=0.0)
    model = random_search_xgb.best_estimator_
    # Prediction button
    if st.button('Predict'):
        # Create a DataFrame for model input
        
        input_data = pd.DataFrame([[TemP, Time_min, PS, BET, PV, C, H, N, O, Biomass_encoded]],
                          columns=['TemP', 'Time (min)', 'PS', 'BET', 'PV', 'C', 'H', 'N', 'O', 'raw_material'])

                                  
    
        # Make prediction using the Random Forest model
        prediction = model.predict(input_data)
    
        # Display prediction
        st.success(f'Predicted Pharmaceutical Removal Efficiency (Qm): {prediction} mg/g')
