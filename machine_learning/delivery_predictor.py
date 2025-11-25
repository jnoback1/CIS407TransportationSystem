"""
Delivery Time Prediction Model
Uses Linear Regression to forecast delivery times based on historical data
Filters out invalid records (Delivery_Time = 0 or unrealistic values)
"""
import logging
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")
    ML_AVAILABLE = False


class DeliveryTimePredictor:
    """Predicts delivery times using Linear Regression"""
    
    def __init__(self, model_path='machine_learning/delivery_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.is_trained = False
        
        # Historical performance dictionaries
        self.store_avg_dict = {}
        self.vehicle_avg_dict = {}
        
        # Model metadata
        self.training_date = None
        self.training_samples = 0
        self.model_version = "2.0"
        
        if os.path.exists(model_path):
            self.load_model()
    
    def prepare_features(self, data):
        """Extract features from order data"""
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)
        
        if len(data) == 0:
            return pd.DataFrame()
        
        features = pd.DataFrame(index=data.index)
        
        # Extract hour from Order_Time
        if 'Order_Hour' in data.columns:
            features['order_hour'] = data['Order_Hour']
        elif 'Order_Time' in data.columns:
            features['order_hour'] = data['Order_Time'].apply(
                lambda x: int(str(x).split(':')[0]) if pd.notna(x) else 12
            )
        else:
            features['order_hour'] = 12
        
        # Day of week
        if 'Day_Of_Week' in data.columns:
            features['day_of_week'] = data['Day_Of_Week']
        elif 'Order_Date' in data.columns:
            dates = pd.to_datetime(data['Order_Date'], errors='coerce')
            features['day_of_week'] = dates.dt.dayofweek.fillna(2)
        else:
            features['day_of_week'] = 2
        
        # Time-based patterns
        features['is_morning_rush'] = ((features['order_hour'] >= 7) & (features['order_hour'] <= 9)).astype(int)
        features['is_lunch_rush'] = ((features['order_hour'] >= 11) & (features['order_hour'] <= 14)).astype(int)
        features['is_dinner_rush'] = ((features['order_hour'] >= 17) & (features['order_hour'] <= 20)).astype(int)
        features['is_late_night'] = ((features['order_hour'] >= 22) | (features['order_hour'] <= 5)).astype(int)
        features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
        
        # Hour squared (non-linear time effects)
        features['hour_squared'] = features['order_hour'] ** 2
        
        # Preparation time if available
        if 'Prep_Time_Minutes' in data.columns:
            features['prep_time'] = pd.to_numeric(data['Prep_Time_Minutes'], errors='coerce').fillna(15)
        else:
            features['prep_time'] = 15
        
        # Historical performance features
        if 'Store_Avg_Time' in data.columns:
            features['store_avg_time'] = pd.to_numeric(data['Store_Avg_Time'], errors='coerce').fillna(147)
        elif hasattr(self, 'store_avg_dict') and self.store_avg_dict and 'StoreID' in data.columns:
            default_avg = 147
            features['store_avg_time'] = data['StoreID'].map(
                lambda x: self.store_avg_dict.get(x, {}).get('avg_time', default_avg)
            )
        else:
            features['store_avg_time'] = 147
        
        if 'Store_Avg_Prep' in data.columns:
            features['store_avg_prep'] = pd.to_numeric(data['Store_Avg_Prep'], errors='coerce').fillna(15)
        elif hasattr(self, 'store_avg_dict') and self.store_avg_dict and 'StoreID' in data.columns:
            features['store_avg_prep'] = data['StoreID'].map(
                lambda x: self.store_avg_dict.get(x, {}).get('avg_prep', 15)
            )
        else:
            features['store_avg_prep'] = 15
        
        if 'Vehicle_Avg_Time' in data.columns:
            features['vehicle_avg_time'] = pd.to_numeric(data['Vehicle_Avg_Time'], errors='coerce').fillna(147)
        elif hasattr(self, 'vehicle_avg_dict') and self.vehicle_avg_dict and 'VehicleID' in data.columns:
            default_avg = 147
            features['vehicle_avg_time'] = data['VehicleID'].map(
                lambda x: self.vehicle_avg_dict.get(x, {}).get('avg_time', default_avg)
            )
        else:
            features['vehicle_avg_time'] = 147
        
        # Interaction features
        features['prep_hour_interaction'] = features['prep_time'] * features['order_hour'] / 100
        features['store_weekend_factor'] = features['store_avg_time'] * features['is_weekend']
        features['vehicle_rush_factor'] = features['vehicle_avg_time'] * (
            features['is_morning_rush'] + features['is_dinner_rush']
        )
        features['weekend_dinner'] = features['is_weekend'] * features['is_dinner_rush']
        
        # New: Add lag features for time series patterns
        if 'Order_Date' in data.columns and len(data) > 1:
            dates = pd.to_datetime(data['Order_Date'], errors='coerce')
            features['days_since_start'] = (dates - dates.min()).dt.days.fillna(0)
            features['month'] = dates.dt.month.fillna(6)
            features['quarter'] = dates.dt.quarter.fillna(2)
        else:
            features['days_since_start'] = 0
            features['month'] = 6
            features['quarter'] = 2
        
        # New: Rush hour intensity score
        features['rush_intensity'] = (
            features['is_morning_rush'] * 1.2 + 
            features['is_lunch_rush'] * 1.5 + 
            features['is_dinner_rush'] * 1.8 +
            features['is_late_night'] * 0.8
        )
        
        # Fill NaN and ensure numeric
        features = features.fillna(0)
        for col in features.columns:
            features[col] = pd.to_numeric(features[col], errors='coerce').fillna(0)
        
        return features
    
    def train(self, training_data):
        """Train the prediction model on historical data"""
        if not ML_AVAILABLE:
            raise ImportError("ML libraries not installed. Run: pip install scikit-learn pandas numpy joblib")
        
        df = pd.DataFrame(training_data)
        
        # Store training metadata
        self.training_date = datetime.now()
        self.training_samples = len(df)
        
        X = self.prepare_features(training_data)
        y = df['Delivery_Time'].values
        
        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError("Cannot extract features from training data")
        
        self.feature_names = X.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Linear Regression
        self.model = LinearRegression()
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        test_pred = self.model.predict(X_test_scaled)
        test_r2 = r2_score(y_test, test_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        
        self.is_trained = True
        
        return {
            'test_r2': test_r2,
            'test_mae': test_mae,
            'samples': len(df),
            'model_type': 'Linear Regression'
        }
    
    def predict(self, order_data):
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        df = pd.DataFrame(order_data) if not isinstance(order_data, pd.DataFrame) else order_data
        X = self.prepare_features(df)
        
        if len(X) == 0:
            raise ValueError("Cannot extract features from order data")
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return np.maximum(predictions, 10)  # Minimum 10 minutes
    
    def predict_with_confidence(self, order_data, confidence=0.95):
        """Make predictions with confidence intervals"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        predictions = self.predict(order_data)
        
        # Use fixed margin based on training error
        margin = 25.0
        return {
            'predictions': predictions,
            'lower_bound': np.maximum(predictions - margin, 10),
            'upper_bound': predictions + margin,
            'confidence': confidence
        }
    
    def save_model(self):
        """Save model to disk"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'store_avg_dict': self.store_avg_dict,
            'vehicle_avg_dict': self.vehicle_avg_dict,
            'trained_date': datetime.now().isoformat(),
            'training_samples': self.training_samples,
            'model_version': self.model_version
        }
        
        joblib.dump(model_data, self.model_path)
    
    def load_model(self):
        """Load model from disk"""
        if not os.path.exists(self.model_path):
            return False
        
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data.get('model')
            self.scaler = model_data.get('scaler')
            self.feature_names = model_data.get('feature_names')
            self.store_avg_dict = model_data.get('store_avg_dict', {})
            self.vehicle_avg_dict = model_data.get('vehicle_avg_dict', {})
            self.training_samples = model_data.get('training_samples', 0)
            self.model_version = model_data.get('model_version', '1.0')
            self.is_trained = True
            
            trained_date = model_data.get('trained_date', 'Unknown')
            logging.info(f"Model loaded (trained: {trained_date}, samples: {self.training_samples})")
            return True
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            return False
    
    def get_feature_importance(self):
        """Get feature importance"""
        if not self.is_trained:
            return []
        
        if hasattr(self.model, 'coef_'):
            importances = np.abs(self.model.coef_)
            feature_importance = list(zip(self.feature_names, importances))
            feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
            return feature_importance
        
        return []


def train_model_from_database():
    """Train model using data from Azure SQL database - filtered for quality"""
    from backend.repository import AzureSqlRepository
    
    repo = AzureSqlRepository()
    
    # CLEAN DATA QUERY - Filter out Delivery_Time = 0 and unrealistic times
    query = """
        SELECT 
            dl.Order_ID,
            CAST(dl.Order_Time AS VARCHAR(8)) AS Order_Time,
            dl.Order_Date,
            dl.VehicleID,
            dl.StoreID,
            dl.Delivery_Time,
            CAST(dl.Pickup_Time AS VARCHAR(8)) AS Pickup_Time,
            DATEDIFF(MINUTE, '00:00:00', dl.Order_Time) AS Order_Time_Minutes,
            DATEDIFF(MINUTE, '00:00:00', dl.Pickup_Time) AS Pickup_Time_Minutes,
            DATEPART(HOUR, dl.Order_Time) AS Order_Hour,
            DATEPART(WEEKDAY, dl.Order_Date) AS Day_Of_Week
        FROM DeliveryLog dl
        WHERE dl.Delivery_Time IS NOT NULL
          AND dl.Delivery_Time > 0
          AND dl.Delivery_Time >= 20
          AND dl.Delivery_Time <= 400
          AND dl.Order_Date >= DATEADD(MONTH, -12, GETDATE())
          AND dl.Pickup_Time IS NOT NULL
          AND dl.Order_Time IS NOT NULL
    """
    
    rows = repo.fetch_all(query)
    
    if not rows or len(rows) < 10:
        repo.close()
        return None, None
    
    # Convert to DataFrame
    training_data = pd.DataFrame(rows, columns=[
        'Order_ID', 'Order_Time', 'Order_Date', 'VehicleID', 
        'StoreID', 'Delivery_Time', 'Pickup_Time', 'Order_Time_Minutes',
        'Pickup_Time_Minutes', 'Order_Hour', 'Day_Of_Week'
    ])
    
    # Calculate prep time
    training_data['Prep_Time_Minutes'] = (
        training_data['Pickup_Time_Minutes'] - training_data['Order_Time_Minutes']
    )
    
    # Handle midnight crossover
    training_data['Prep_Time_Minutes'] = training_data['Prep_Time_Minutes'].apply(
        lambda x: x if x >= 0 else x + 1440
    )
    
    # Filter out unrealistic prep times
    training_data = training_data[
        (training_data['Prep_Time_Minutes'] >= 0) & 
        (training_data['Prep_Time_Minutes'] <= 120)
    ]
    
    # Get store performance statistics
    store_stats_query = """
        SELECT 
            StoreID,
            AVG(CAST(Delivery_Time AS FLOAT)) as Avg_Delivery_Time,
            COUNT(*) as Total_Deliveries
        FROM DeliveryLog
        WHERE Delivery_Time IS NOT NULL 
          AND Delivery_Time > 0
          AND Delivery_Time >= 20
          AND Delivery_Time <= 400
        GROUP BY StoreID
    """
    store_stats = repo.fetch_all(store_stats_query)
    
    # Get vehicle performance statistics
    vehicle_stats_query = """
        SELECT 
            VehicleID,
            AVG(CAST(Delivery_Time AS FLOAT)) as Avg_Delivery_Time,
            COUNT(*) as Total_Deliveries
        FROM DeliveryLog
        WHERE Delivery_Time IS NOT NULL 
          AND Delivery_Time > 0
          AND Delivery_Time >= 20
          AND Delivery_Time <= 400
        GROUP BY VehicleID
    """
    vehicle_stats = repo.fetch_all(vehicle_stats_query)
    
    repo.close()
    
    # Calculate store average prep time
    store_prep_avg = training_data.groupby('StoreID')['Prep_Time_Minutes'].mean().to_dict()
    
    # Create lookup dictionaries
    store_avg_dict = {}
    for row in store_stats:
        store_id = row['StoreID']
        store_avg_dict[store_id] = {
            'avg_time': row['Avg_Delivery_Time'],
            'total': row['Total_Deliveries'],
            'avg_prep': store_prep_avg.get(store_id, 15)
        }
    
    vehicle_avg_dict = {}
    for row in vehicle_stats:
        vehicle_avg_dict[row['VehicleID']] = {
            'avg_time': row['Avg_Delivery_Time'],
            'total': row['Total_Deliveries']
        }
    
    # Add historical performance features
    training_data['Store_Avg_Time'] = training_data['StoreID'].map(
        lambda x: store_avg_dict.get(x, {}).get('avg_time', training_data['Delivery_Time'].mean())
    )
    
    training_data['Store_Avg_Prep'] = training_data['StoreID'].map(
        lambda x: store_avg_dict.get(x, {}).get('avg_prep', 15)
    )
    
    training_data['Vehicle_Avg_Time'] = training_data['VehicleID'].map(
        lambda x: vehicle_avg_dict.get(x, {}).get('avg_time', training_data['Delivery_Time'].mean())
    )
    
    predictor = DeliveryTimePredictor()
    predictor.store_avg_dict = store_avg_dict
    predictor.vehicle_avg_dict = vehicle_avg_dict
    
    metrics = predictor.train(training_data)
    predictor.save_model()
    
    return predictor, metrics


if __name__ == "__main__":
    if not ML_AVAILABLE:
        print("ML libraries not installed. Run: pip install scikit-learn pandas numpy joblib")
        sys.exit(1)
    
    predictor, metrics = train_model_from_database()
    
    if predictor and metrics:
        print(f"R² Score: {metrics['test_r2']:.3f}")
        print(f"MAE: {metrics['test_mae']:.2f} minutes")
    else:
        print("Training failed.")