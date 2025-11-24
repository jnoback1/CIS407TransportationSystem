"""
Delivery Time Prediction Model
Uses Ridge Regression to forecast delivery times based on historical data
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
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")
    ML_AVAILABLE = False


class DeliveryTimePredictor:
    """Predicts delivery times using regression models"""
    
    def __init__(self, model_path='machine_learning/delivery_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.is_trained = False
        
        # Simple time-based fallback
        self.hour_averages = {}
        self.day_averages = {}
        self.overall_average = 147.0
        self.use_simple_model = False
        
        # Historical performance dictionaries
        self.store_avg_dict = {}
        self.vehicle_avg_dict = {}
        
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
        
        # Fill NaN and ensure numeric
        features = features.fillna(0)
        for col in features.columns:
            features[col] = pd.to_numeric(features[col], errors='coerce').fillna(0)
        
        return features
    
    def train(self, training_data):
        """Train the prediction model on historical data"""
        if not ML_AVAILABLE:
            raise ImportError("ML libraries not installed. Run: pip install scikit-learn pandas numpy joblib")
        
        print(f"Training model with {len(training_data)} samples...")
        
        # Calculate simple averages as fallback
        df = pd.DataFrame(training_data)
        df['hour'] = df['Order_Time'].apply(
            lambda x: int(str(x).split(':')[0]) if pd.notna(x) else 12
        )
        self.hour_averages = df.groupby('hour')['Delivery_Time'].mean().to_dict()
        self.overall_average = df['Delivery_Time'].mean()
        
        print(f"   Overall average delivery time: {self.overall_average:.2f} minutes")
        print(f"   Delivery time std dev: {df['Delivery_Time'].std():.2f} minutes")
        
        # Try ML training
        try:
            X = self.prepare_features(training_data)
            y = df['Delivery_Time'].values
            
            if X.shape[0] == 0 or X.shape[1] == 0:
                print("⚠️  Could not extract features, using simple time-based model")
                self.use_simple_model = True
                self.is_trained = True
                return self._get_simple_metrics(df)
            
            self.feature_names = X.columns.tolist()
            print(f"   Features: {len(self.feature_names)}")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=True
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Try Ridge Regression first
            ridge_model = Ridge(alpha=10.0, random_state=42)
            ridge_model.fit(X_train_scaled, y_train)
            
            ridge_test_pred = ridge_model.predict(X_test_scaled)
            ridge_test_r2 = r2_score(y_test, ridge_test_pred)
            ridge_test_mae = mean_absolute_error(y_test, ridge_test_pred)
            
            print(f"   Ridge Regression - Test R²: {ridge_test_r2:.3f}, MAE: {ridge_test_mae:.2f}")
            
            # If Ridge is decent, use it
            if ridge_test_r2 > 0.1:
                self.model = ridge_model
                self.use_simple_model = False
                self.is_trained = True
                
                train_pred = ridge_model.predict(X_train_scaled)
                train_r2 = r2_score(y_train, train_pred)
                train_mae = mean_absolute_error(y_train, train_pred)
                
                print(f"Using Ridge Regression model")
                
                return {
                    'train_r2': train_r2,
                    'test_r2': ridge_test_r2,
                    'train_mae': train_mae,
                    'test_mae': ridge_test_mae,
                    'samples': len(df),
                    'model_type': 'Ridge Regression'
                }
            
            # Try Random Forest if Ridge is weak
            print("   Ridge weak, trying Random Forest...")
            rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
            rf_model.fit(X_train_scaled, y_train)
            
            rf_test_pred = rf_model.predict(X_test_scaled)
            rf_test_r2 = r2_score(y_test, rf_test_pred)
            rf_test_mae = mean_absolute_error(y_test, rf_test_pred)
            
            print(f"   Random Forest - Test R²: {rf_test_r2:.3f}, MAE: {rf_test_mae:.2f}")
            
            if rf_test_r2 > ridge_test_r2 and rf_test_r2 > 0:
                self.model = rf_model
                self.use_simple_model = False
                self.is_trained = True
                
                rf_train_pred = rf_model.predict(X_train_scaled)
                train_r2 = r2_score(y_train, rf_train_pred)
                train_mae = mean_absolute_error(y_train, rf_train_pred)
                
                print(f"Using Random Forest model")
                
                return {
                    'train_r2': train_r2,
                    'test_r2': rf_test_r2,
                    'train_mae': train_mae,
                    'test_mae': rf_test_mae,
                    'samples': len(df),
                    'model_type': 'Random Forest'
                }
            
            # Fall back to simple model if both ML models fail
            raise ValueError("ML models not effective (R² <= 0)")
            
        except Exception as e:
            print(f"  ML training failed: {e}")
            print("   Falling back to simple time-based model")
            self.use_simple_model = True
            self.is_trained = True
            return self._get_simple_metrics(df)
    
    def _get_simple_metrics(self, df):
        """Calculate metrics for simple time-based model"""
        predictions = []
        for _, row in df.iterrows():
            hour = int(str(row.get('Order_Time', '12:00')).split(':')[0])
            pred = self.hour_averages.get(hour, self.overall_average)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        mae = mean_absolute_error(df['Delivery_Time'].values, predictions)
        r2 = r2_score(df['Delivery_Time'].values, predictions)
        
        return {
            'train_r2': r2,
            'test_r2': r2,
            'train_mae': mae,
            'test_mae': mae,
            'samples': len(df),
            'model_type': 'Simple Time-Based'
        }
    
    def predict(self, order_data):
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        if self.use_simple_model:
            return self._predict_simple(order_data)
        
        df = pd.DataFrame(order_data) if not isinstance(order_data, pd.DataFrame) else order_data
        X = self.prepare_features(df)
        
        if len(X) == 0:
            return np.array([self.overall_average] * len(df))
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return np.maximum(predictions, 10)  # Minimum 10 minutes
    
    def _predict_simple(self, order_data):
        """Simple time-based predictions"""
        df = pd.DataFrame(order_data) if not isinstance(order_data, pd.DataFrame) else order_data
        
        predictions = []
        for _, row in df.iterrows():
            if 'Order_Hour' in row:
                hour = row['Order_Hour']
            elif 'Order_Time' in row:
                hour = int(str(row['Order_Time']).split(':')[0])
            else:
                hour = 12
            
            pred = self.hour_averages.get(hour, self.overall_average)
            predictions.append(pred)
        
        return np.array(predictions)
    
    def save_model(self):
        """Save model to disk"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'hour_averages': self.hour_averages,
            'day_averages': self.day_averages,
            'overall_average': self.overall_average,
            'use_simple_model': self.use_simple_model,
            'store_avg_dict': self.store_avg_dict,
            'vehicle_avg_dict': self.vehicle_avg_dict,
            'trained_date': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, self.model_path)
        logging.info(f"Model saved to {self.model_path}")
        print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load model from disk"""
        if not os.path.exists(self.model_path):
            return False
        
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data.get('model')
            self.scaler = model_data.get('scaler')
            self.feature_names = model_data.get('feature_names')
            self.hour_averages = model_data.get('hour_averages', {})
            self.day_averages = model_data.get('day_averages', {})
            self.overall_average = model_data.get('overall_average', 147.0)
            self.use_simple_model = model_data.get('use_simple_model', False)
            self.store_avg_dict = model_data.get('store_avg_dict', {})
            self.vehicle_avg_dict = model_data.get('vehicle_avg_dict', {})
            self.is_trained = True
            
            trained_date = model_data.get('trained_date', 'Unknown')
            logging.info(f"Model loaded (trained: {trained_date})")
            return True
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            return False
    
    def get_feature_importance(self):
        """Get feature importance"""
        if not self.is_trained or self.use_simple_model:
            return [('order_hour', 1.0)]
        
        if hasattr(self.model, 'feature_importances_'):
            # Random Forest
            importances = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            # Ridge
            importances = np.abs(self.model.coef_)
        else:
            return []
        
        feature_importance = list(zip(self.feature_names, importances))
        feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return feature_importance


def train_model_from_database():
    """Train model using data from Azure SQL database - filtered for quality"""
    from backend.repository import AzureSqlRepository
    
    repo = AzureSqlRepository()
    
    print("Fetching delivery data from Azure SQL...")
    
    #CLEAN DATA QUERY - Filter out Delivery_Time = 0 and unrealistic times
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
        print(f"Insufficient valid data. Found: {len(rows) if rows else 0} records")
        print("   Need at least 10 valid deliveries with times between 20-400 minutes")
        repo.close()
        return None, None
    
    # Convert to DataFrame
    training_data = pd.DataFrame(rows, columns=[
        'Order_ID', 'Order_Time', 'Order_Date', 'VehicleID', 
        'StoreID', 'Delivery_Time', 'Pickup_Time', 'Order_Time_Minutes',
        'Pickup_Time_Minutes', 'Order_Hour', 'Day_Of_Week'
    ])
    
    # Calculate prep time in Python (safer than SQL)
    training_data['Prep_Time_Minutes'] = (
        training_data['Pickup_Time_Minutes'] - training_data['Order_Time_Minutes']
    )
    
    # Handle midnight crossover
    training_data['Prep_Time_Minutes'] = training_data['Prep_Time_Minutes'].apply(
        lambda x: x if x >= 0 else x + 1440
    )
    
    # ✅ Filter out unrealistic prep times
    training_data = training_data[
        (training_data['Prep_Time_Minutes'] >= 0) & 
        (training_data['Prep_Time_Minutes'] <= 120)
    ]
    
    print(f"   Found {len(training_data)} valid delivery records")
    print(f"   Delivery time range: {training_data['Delivery_Time'].min():.0f} - {training_data['Delivery_Time'].max():.0f} minutes")
    print(f"   Average delivery time: {training_data['Delivery_Time'].mean():.1f} minutes")
    print(f"   Std deviation: {training_data['Delivery_Time'].std():.1f} minutes")
    print(f"   Average prep time: {training_data['Prep_Time_Minutes'].mean():.1f} minutes")
    
    # Get store performance statistics - with quality filter
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
    
    # Get vehicle performance statistics - with quality filter
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
    
    # Calculate store average prep time in Python
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
    
    print(f"   Stores in dataset: {training_data['StoreID'].nunique()}")
    print(f"   Vehicles in dataset: {training_data['VehicleID'].nunique()}")
    
    predictor = DeliveryTimePredictor()
    predictor.store_avg_dict = store_avg_dict
    predictor.vehicle_avg_dict = vehicle_avg_dict
    
    metrics = predictor.train(training_data)
    predictor.save_model()
    
    return predictor, metrics


if __name__ == "__main__":
    if not ML_AVAILABLE:
        print("    ML libraries not installed. Run: pip install scikit-learn pandas numpy joblib")
        sys.exit(1)
    
    print("    Training delivery time prediction model...")
    print("=" * 60)
    predictor, metrics = train_model_from_database()
    
    if predictor and metrics:
        print("\n" + "=" * 60)
        print("    Model training complete!")
        print(f"   Model Type: {metrics['model_type']}")
        print(f"   Test R²: {metrics['test_r2']:.3f}")
        print(f"   Test MAE: {metrics['test_mae']:.2f} minutes")
        print(f"   Training Samples: {metrics['samples']}")
        print("\n    Model saved and ready to use!")
        print("\nRestart your application and navigate to the Analytics tab")
        print("to see AI-powered delivery time predictions!")
    else:
        print("\n    Model training failed. Check data quality.")