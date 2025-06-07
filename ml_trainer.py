"""
🤖 PET HEALTH ML TRAINING SYSTEM
Advanced Machine Learning for Pet Health Diagnosis Prediction
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import sqlite3
from datetime import datetime
import json
import config
from utils.database import db

class PetHealthMLTrainer:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.model_path = "data/pet_health_model.pkl"
        self.encoders_path = "data/label_encoders.pkl"
        self.scaler_path = "data/scaler.pkl"
        
    def prepare_training_data(self):
        """Prepare training data from database"""
        print("🔄 جمع‌آوری داده‌های آموزشی...")
        
        # Get all health data with pet info
        try:
            training_data = db.get_ml_training_data()
        except Exception as e:
            print(f"❌ خطا در دسترسی به داده‌ها: {e}")
            print("💡 ایجاد داده‌های نمونه برای آموزش...")
            return self.create_sample_data()
        
        if not training_data:
            print("❌ داده‌ای برای آموزش یافت نشد!")
            print("💡 ایجاد داده‌های نمونه برای آموزش...")
            return self.create_sample_data()
        
        # Convert to DataFrame
        columns = [
            'health_id', 'pet_id', 'log_date', 'weight', 'food_type', 'mood', 
            'stool_info', 'appetite', 'water_intake', 'activity_level', 'notes',
            'symptoms', 'sleep_hours', 'medication_taken', 'temperature', 
            'breathing', 'blood_test_image', 'vet_note_image', 'pet_image',
            'species', 'breed', 'age_years', 'base_weight', 'gender'
        ]
        
        df = pd.DataFrame(training_data, columns=columns)
        
        # Create target variable (health risk level)
        df['risk_level'] = self.calculate_risk_level(df)
        
        # Feature engineering
        df = self.engineer_features(df)
        
        # Select features for training
        feature_cols = [
            'weight_change_percent', 'age_years', 'mood_encoded', 'stool_encoded',
            'appetite_encoded', 'water_encoded', 'activity_encoded', 'temperature_encoded',
            'breathing_encoded', 'species_encoded', 'gender_encoded', 'sleep_hours',
            'has_symptoms', 'has_images'
        ]
        
        # Remove rows with missing target
        df = df.dropna(subset=['risk_level'])
        
        X = df[feature_cols].fillna(0)
        y = df['risk_level']
        
        self.feature_columns = feature_cols
        
        print(f"✅ آماده‌سازی {len(df)} نمونه داده")
        return X, y
    
    def calculate_risk_level(self, df):
        """Calculate risk level based on health indicators"""
        risk_scores = []
        
        for _, row in df.iterrows():
            risk = 0
            
            # Weight change risk
            if pd.notna(row['weight']) and pd.notna(row['base_weight']):
                weight_change = abs(row['weight'] - row['base_weight']) / row['base_weight'] * 100
                if weight_change > 10:
                    risk += 3
                elif weight_change > 5:
                    risk += 2
                elif weight_change > 2:
                    risk += 1
            
            # Mood risk
            if row['mood'] in ['خسته و بی‌حال', 'اضطراب']:
                risk += 2
            
            # Stool risk
            if row['stool_info'] == 'خونی':
                risk += 3
            elif row['stool_info'] in ['نرم', 'سفت']:
                risk += 1
            
            # Appetite risk
            if row['appetite'] == 'بدون اشتها':
                risk += 2
            elif row['appetite'] == 'کم':
                risk += 1
            
            # Activity risk
            if row['activity_level'] == 'کم':
                risk += 1
            
            # Temperature risk
            if row['temperature'] in ['تب', 'داغ']:
                risk += 2
            elif row['temperature'] == 'سرد':
                risk += 1
            
            # Breathing risk
            if row['breathing'] in ['سریع', 'سرفه', 'صدادار']:
                risk += 2
            elif row['breathing'] == 'آهسته':
                risk += 1
            
            # Age risk
            if pd.notna(row['age_years']) and row['age_years'] > 10:
                risk += 1
            
            # Categorize risk
            if risk >= 8:
                risk_level = 3  # Critical
            elif risk >= 5:
                risk_level = 2  # High
            elif risk >= 2:
                risk_level = 1  # Medium
            else:
                risk_level = 0  # Low
            
            risk_scores.append(risk_level)
        
        return risk_scores
    
    def engineer_features(self, df):
        """Engineer features for ML model"""
        # Weight change percentage
        df['weight_change_percent'] = 0
        mask = pd.notna(df['weight']) & pd.notna(df['base_weight']) & (df['base_weight'] > 0)
        df.loc[mask, 'weight_change_percent'] = abs(df.loc[mask, 'weight'] - df.loc[mask, 'base_weight']) / df.loc[mask, 'base_weight'] * 100
        
        # Encode categorical variables
        categorical_cols = ['mood', 'stool_info', 'appetite', 'water_intake', 'activity_level', 
                          'temperature', 'breathing', 'species', 'gender']
        
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            
            # Fill missing values
            df[col] = df[col].fillna('نامشخص')
            
            # Fit and transform
            try:
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            except:
                # Handle new categories
                df[f'{col}_encoded'] = 0
        
        # Binary features
        df['has_symptoms'] = (df['symptoms'].notna() & (df['symptoms'] != 'ندارد')).astype(int)
        df['has_images'] = ((df['blood_test_image'].notna()) | 
                           (df['vet_note_image'].notna()) | 
                           (df['pet_image'].notna())).astype(int)
        
        return df
    
    def train_model(self, X, y):
        """Train the ML model"""
        print("🤖 شروع آموزش مدل...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ دقت مدل: {accuracy:.2%}")
        print("\n📊 گزارش تفصیلی:")
        print(classification_report(y_test, y_pred, 
                                  target_names=['کم خطر', 'متوسط', 'پرخطر', 'بحرانی']))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔍 اهمیت ویژگی‌ها:")
        for _, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']}: {row['importance']:.3f}")
        
        return accuracy
    
    def save_model(self):
        """Save trained model and encoders"""
        print("💾 ذخیره مدل...")
        
        # Create data directory if not exists
        import os
        os.makedirs('data', exist_ok=True)
        
        # Save model
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.label_encoders, self.encoders_path)
        joblib.dump(self.scaler, self.scaler_path)
        
        # Save metadata
        metadata = {
            'trained_at': datetime.now().isoformat(),
            'feature_columns': self.feature_columns,
            'model_type': 'RandomForestClassifier'
        }
        
        with open('data/model_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print("✅ مدل با موفقیت ذخیره شد!")
    
    def load_model(self):
        """Load trained model"""
        try:
            self.model = joblib.load(self.model_path)
            self.label_encoders = joblib.load(self.encoders_path)
            self.scaler = joblib.load(self.scaler_path)
            
            with open('data/model_metadata.json', 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.feature_columns = metadata['feature_columns']
            
            print("✅ مدل بارگذاری شد!")
            return True
        except Exception as e:
            print(f"❌ خطا در بارگذاری مدل: {e}")
            return False
    
    def predict_health_risk(self, pet_data, health_data):
        """Predict health risk for a pet"""
        if not self.model:
            if not self.load_model():
                return None, "مدل در دسترس نیست"
        
        try:
            # Prepare features
            features = self.prepare_prediction_features(pet_data, health_data)
            
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Predict
            risk_level = self.model.predict(features_scaled)[0]
            risk_probability = self.model.predict_proba(features_scaled)[0]
            
            risk_names = ['کم خطر', 'متوسط', 'پرخطر', 'بحرانی']
            
            return {
                'risk_level': int(risk_level),
                'risk_name': risk_names[risk_level],
                'confidence': float(max(risk_probability)),
                'probabilities': {
                    risk_names[i]: float(prob) 
                    for i, prob in enumerate(risk_probability)
                }
            }, None
            
        except Exception as e:
            return None, f"خطا در پیش‌بینی: {str(e)}"
    
    def prepare_prediction_features(self, pet_data, health_data):
        """Prepare features for prediction"""
        features = [0] * len(self.feature_columns)
        
        # Map features
        feature_map = {
            'weight_change_percent': 0,
            'age_years': pet_data.get('age_years', 0),
            'sleep_hours': health_data.get('sleep_hours', 8),
            'has_symptoms': 1 if health_data.get('symptoms') and health_data.get('symptoms') != 'ندارد' else 0,
            'has_images': 1 if any([health_data.get('blood_test_image'), 
                                   health_data.get('vet_note_image'), 
                                   health_data.get('pet_image')]) else 0
        }
        
        # Calculate weight change
        if health_data.get('weight') and pet_data.get('base_weight'):
            feature_map['weight_change_percent'] = abs(health_data['weight'] - pet_data['base_weight']) / pet_data['base_weight'] * 100
        
        # Encode categorical features
        categorical_features = {
            'mood_encoded': health_data.get('mood', 'نامشخص'),
            'stool_encoded': health_data.get('stool_info', 'نامشخص'),
            'appetite_encoded': health_data.get('appetite', 'نامشخص'),
            'water_encoded': health_data.get('water_intake', 'نامشخص'),
            'activity_encoded': health_data.get('activity_level', 'نامشخص'),
            'temperature_encoded': health_data.get('temperature', 'نامشخص'),
            'breathing_encoded': health_data.get('breathing', 'نامشخص'),
            'species_encoded': pet_data.get('species', 'نامشخص'),
            'gender_encoded': pet_data.get('gender', 'نامشخص')
        }
        
        for feature, value in categorical_features.items():
            base_feature = feature.replace('_encoded', '')
            if base_feature in self.label_encoders:
                try:
                    encoded_value = self.label_encoders[base_feature].transform([value])[0]
                    feature_map[feature] = encoded_value
                except:
                    feature_map[feature] = 0
        
        # Fill feature vector
        for i, col in enumerate(self.feature_columns):
            if col in feature_map:
                features[i] = feature_map[col]
        
        return features
    
    def create_sample_data(self):
        """Create sample data for ML training when no real data exists"""
        print("🔄 ایجاد داده‌های نمونه...")
        
        # Create sample data
        sample_data = []
        moods = ['شاد و پرانرژی', 'عادی', 'خسته و بی‌حال', 'اضطراب']
        stools = ['طبیعی', 'نرم', 'سفت', 'خونی']
        appetites = ['زیاد', 'نرمال', 'کم', 'بدون اشتها']
        waters = ['زیاد', 'نرمال', 'کم', 'نمی‌نوشد']
        activities = ['زیاد', 'متوسط', 'کم']
        temperatures = ['نرمال', 'داغ', 'سرد', 'تب']
        breathings = ['نرمال', 'سریع', 'آهسته', 'سرفه', 'صدادار']
        species = ['سگ', 'گربه', 'خرگوش']
        genders = ['نر', 'ماده']
        
        # Generate 100 sample records
        np.random.seed(42)
        for i in range(100):
            mood = np.random.choice(moods)
            stool = np.random.choice(stools)
            appetite = np.random.choice(appetites)
            water = np.random.choice(waters)
            activity = np.random.choice(activities)
            temp = np.random.choice(temperatures)
            breathing = np.random.choice(breathings)
            spec = np.random.choice(species)
            gender = np.random.choice(genders)
            
            # Calculate risk based on conditions
            risk = 0
            if mood in ['خسته و بی‌حال', 'اضطراب']:
                risk += 2
            if stool == 'خونی':
                risk += 3
            elif stool in ['نرم', 'سفت']:
                risk += 1
            if appetite in ['کم', 'بدون اشتها']:
                risk += 2
            if activity == 'کم':
                risk += 1
            if temp in ['تب', 'داغ']:
                risk += 2
            if breathing in ['سریع', 'سرفه', 'صدادار']:
                risk += 2
            
            # Categorize risk
            if risk >= 8:
                risk_level = 3
            elif risk >= 5:
                risk_level = 2
            elif risk >= 2:
                risk_level = 1
            else:
                risk_level = 0
            
            sample_data.append({
                'mood': mood,
                'stool_info': stool,
                'appetite': appetite,
                'water_intake': water,
                'activity_level': activity,
                'temperature': temp,
                'breathing': breathing,
                'species': spec,
                'gender': gender,
                'age_years': np.random.randint(1, 15),
                'weight_change_percent': np.random.uniform(0, 15),
                'sleep_hours': np.random.randint(6, 12),
                'has_symptoms': np.random.choice([0, 1]),
                'has_images': np.random.choice([0, 1]),
                'risk_level': risk_level
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(sample_data)
        
        # Encode categorical variables
        categorical_cols = ['mood', 'stool_info', 'appetite', 'water_intake', 'activity_level', 
                          'temperature', 'breathing', 'species', 'gender']
        
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
        
        # Select features
        feature_cols = [
            'weight_change_percent', 'age_years', 'mood_encoded', 'stool_encoded',
            'appetite_encoded', 'water_encoded', 'activity_encoded', 'temperature_encoded',
            'breathing_encoded', 'species_encoded', 'gender_encoded', 'sleep_hours',
            'has_symptoms', 'has_images'
        ]
        
        self.feature_columns = feature_cols
        
        X = df[feature_cols]
        y = df['risk_level']
        
        print(f"✅ ایجاد {len(df)} نمونه داده آموزشی")
        return X, y

def train_pet_health_model():
    """Main training function"""
    print("🚀 شروع آموزش مدل هوش مصنوعی سلامت حیوانات")
    print("=" * 60)
    
    trainer = PetHealthMLTrainer()
    
    # Prepare data
    X, y = trainer.prepare_training_data()
    
    if X is None:
        print("❌ عدم وجود داده کافی برای آموزش")
        return False
    
    # Train model
    accuracy = trainer.train_model(X, y)
    
    if accuracy > 0.7:  # Only save if accuracy is good
        trainer.save_model()
        print(f"\n🎉 مدل با دقت {accuracy:.2%} آموزش داده شد!")
        return True
    else:
        print(f"\n⚠️ دقت مدل ({accuracy:.2%}) کافی نیست. نیاز به داده بیشتر.")
        return False

if __name__ == "__main__":
    train_pet_health_model()
