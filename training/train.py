import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from xgboost import XGBRegressor
import joblib
import os
from datetime import datetime

# Define file paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'indian_railway_delay_data_.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'railpulse_eta_model.pkl')

def time_to_minutes(time_str):
    try:
        h, m, s = map(int, time_str.strip().split(':'))
        return h * 60 + m + s / 60.0
    except:
        return 0.0

def load_and_preprocess_data(filepath):
    df = pd.read_csv(filepath)
    
    # Clean column names
    df.columns = [col.strip() for col in df.columns]
    
    expanded_rows = []
    
    # Progress intervals
    progress_points = [0.0, 0.25, 0.5, 0.75, 0.9]
    
    for _, row in df.iterrows():
        # Parse times
        time_str_parts = str(row['Sc_arr__time']).strip().split()
        time_part = time_str_parts[-1] if time_str_parts else "00:00:00"
        scheduled_arrival_hour = int(time_part.split(':')[0])
        
        delay_mins = time_to_minutes(row['Dealy_min'])
        
        # Assume an average speed to get total scheduled time (e.g., 60 km/h)
        total_distance = float(row['Distance(Km)'])
        avg_speed = 60.0 
        scheduled_total_time = (total_distance / avg_speed) * 60 # in minutes
        
        for p in progress_points:
            distance_remaining = total_distance * (1 - p)
            elapsed_time = scheduled_total_time * p
            current_delay = delay_mins * p # delay accumulates
            
            remaining_travel_time = (scheduled_total_time * (1 - p)) + (delay_mins * (1 - p))
            
            expanded_rows.append({
                'train_number': str(row['Train_no']),
                'train_type': 'Express',
                'train_priority': 1,
                'source': row['Source'],
                'destination': row['Destitnation'],
                'distance_remaining_km': distance_remaining,
                'current_speed_kmph': avg_speed * (0.8 + 0.4 * np.random.rand()), 
                'current_delay_minutes': current_delay,
                'scheduled_arrival_hour': scheduled_arrival_hour,
                'season': row['Season'],
                'run_frequency': row['Run_frequency'],
                'target_remaining_minutes': remaining_travel_time,
                'target_delay_minutes': delay_mins
            })
            
    return pd.DataFrame(expanded_rows)

def build_and_train_model(df):
    X = df.drop(columns=['target_remaining_minutes', 'target_delay_minutes'])
    y_remaining = df['target_remaining_minutes']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_remaining, test_size=0.2, random_state=42)
    
    numeric_features = ['distance_remaining_km', 'current_speed_kmph', 'current_delay_minutes', 'scheduled_arrival_hour']
    categorical_features = ['train_number', 'train_type', 'source', 'destination', 'season', 'run_frequency']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42))
    ])
    
    pipeline.fit(X_train, y_train)
    
    score = pipeline.score(X_test, y_test)
    print(f"ETA Model R2 Score on Test Set: {score:.4f}")
    
    y_delay_train = df.loc[X_train.index, 'target_delay_minutes']
    
    delay_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42))
    ])
    delay_pipeline.fit(X_train, y_delay_train)
    
    model_bundle = {
        'eta_pipeline': pipeline,
        'delay_pipeline': delay_pipeline,
        'metadata': {
            'version': 'eta-v1',
            'trained_at': datetime.now().isoformat(),
            'features': numeric_features + categorical_features,
            'metrics': {'r2_eta': score}
        }
    }
    
    joblib.dump(model_bundle, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == '__main__':
    print("Loading data...")
    df = load_and_preprocess_data(DATA_PATH)
    print("Training model...")
    build_and_train_model(df)
