import sqlite3
import asyncio
from datetime import datetime
import config

class Database:
    def __init__(self):
        self.db_path = config.DATABASE_PATH
        self.init_db()
    
    def init_db(self):
        """Initialize database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Pets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pets (
                pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT,
                age_years INTEGER,
                age_months INTEGER,
                weight REAL,
                gender TEXT,
                is_neutered BOOLEAN,
                diseases TEXT,
                medications TEXT,
                vaccine_status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Enhanced Health logs table with learning capabilities
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            date TEXT,
            weight REAL,
            food_type TEXT,
            food_intake_notes TEXT,
            diet_changes TEXT,
            mood TEXT,
            stool_info TEXT,
            appetite TEXT,
            water_intake TEXT,
            activity_level TEXT,
            activity_duration INTEGER,
            activity_changes TEXT,
            sleep_hours INTEGER,
            sleep_quality TEXT,
            notes TEXT,
            symptoms TEXT,
            medication_taken BOOLEAN,
            temperature TEXT,
            breathing TEXT,
            blood_test_image TEXT,
            vet_note_image TEXT,
            pet_image TEXT,
            ai_analysis TEXT,
            risk_factors TEXT,
            correlation_flags TEXT,
            FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
        )
        ''')
        
        # AI feedback table for learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pet_id INTEGER,
                consultation_id TEXT,
                ai_type TEXT,
                rating INTEGER,
                feedback_type TEXT,
                detailed_feedback TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
            )
        ''')
        
        # AI learning patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_learning_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_id INTEGER,
                pattern_type TEXT,
                pattern_data TEXT,
                confidence_score REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
            )
        ''')
        
        # Task tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_logs (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_id INTEGER,
                task_type TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
            )
        ''')
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                is_premium BOOLEAN DEFAULT FALSE,
                subscription_type TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                payment_reference TEXT,
                is_trial BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # AI usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                usage_date DATE,
                message_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, usage_date)
            )
        ''')
        
        # Diet plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diet_plans (
                plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pet_id INTEGER,
                diet_type TEXT,
                goal TEXT,
                allergies TEXT,
                budget TEXT,
                preference TEXT,
                generated_plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
            )
        ''')
        
        # AI insights table - stores AI analysis results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_insights (
                insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_id INTEGER,
                log_date TEXT,
                ai_summary TEXT,
                extracted_tags TEXT,
                risk_score INTEGER,
                model_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
            )
        ''')
        
        # AI chat sessions table - stores complete chat interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pet_id INTEGER,
                log_date TEXT,
                user_message TEXT,
                ai_response TEXT,
                model_name TEXT,
                session_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username):
        """Add new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                      (user_id, username))
        conn.commit()
        conn.close()
    
    def add_pet(self, user_id, pet_data):
        """Add new pet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pets (user_id, name, species, breed, age_years, age_months, 
                            weight, gender, is_neutered, diseases, medications, vaccine_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, pet_data['name'], pet_data['species'], pet_data['breed'],
              pet_data['age_years'], pet_data['age_months'], pet_data['weight'],
              pet_data['gender'], pet_data['is_neutered'], pet_data['diseases'],
              pet_data['medications'], pet_data['vaccine_status']))
        pet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pet_id
    
    def get_user_pets(self, user_id):
        """Get all pets for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pets WHERE user_id = ?', (user_id,))
        pets = cursor.fetchall()
        conn.close()
        return pets
    
    def add_health_log(self, pet_id, health_data):
        """Add health log entry with image support"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO health_logs (pet_id, date, weight, food_type, food_intake_notes, diet_changes,
                                   mood, stool_info, appetite, water_intake, activity_level, activity_duration,
                                   activity_changes, sleep_hours, sleep_quality, notes, symptoms, 
                                   medication_taken, temperature, breathing, blood_test_image, 
                                   vet_note_image, pet_image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pet_id, 
            datetime.now().strftime('%Y-%m-%d'), 
            health_data.get('weight'), 
            health_data.get('food_type', 'عادی'),
            health_data.get('food_intake_notes', ''),
            health_data.get('diet_changes', ''),
            health_data.get('mood'), 
            health_data.get('stool_info'), 
            health_data.get('appetite', ''),
            health_data.get('water_intake', ''),
            health_data.get('activity_level'),
            health_data.get('activity_duration', 0),
            health_data.get('activity_changes', ''),
            health_data.get('sleep_hours', 8), 
            health_data.get('sleep_quality', ''),
            health_data.get('notes', ''),
            health_data.get('symptoms', 'ندارد'),
            health_data.get('medication_taken', False),
            health_data.get('temperature', ''),
            health_data.get('breathing', ''),
            health_data.get('blood_test_image', ''),
            health_data.get('vet_note_image', ''),
            health_data.get('pet_image', '')
        ))
        conn.commit()
        conn.close()
    
    def save_image(self, file_id, image_type, pet_id=None):
        """Save image file_id for later retrieval"""
        # Store image reference in a simple way
        return f"{image_type}_{pet_id}_{file_id}" if pet_id else f"{image_type}_{file_id}"
    
    def get_ml_training_data(self):
        """Get all health data for ML training"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, p.species, p.breed, p.age_years, p.weight as base_weight, p.gender
            FROM health_logs h
            JOIN pets p ON h.pet_id = p.pet_id
            ORDER BY h.date DESC
        ''')
        data = cursor.fetchall()
        conn.close()
        return data
    
    def add_diagnosis_record(self, pet_id, symptoms, diagnosis, treatment, outcome):
        """Add diagnosis record for ML training"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnosis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_id INTEGER,
                symptoms TEXT,
                diagnosis TEXT,
                treatment TEXT,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
            )
        ''')
        cursor.execute('''
            INSERT INTO diagnosis_records (pet_id, symptoms, diagnosis, treatment, outcome)
            VALUES (?, ?, ?, ?, ?)
        ''', (pet_id, symptoms, diagnosis, treatment, outcome))
        conn.commit()
        conn.close()
    
    def get_pet_health_logs(self, pet_id, limit=10):
        """Get recent health logs for pet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM health_logs WHERE pet_id = ? ORDER BY date DESC LIMIT ?', 
                      (pet_id, limit))
        logs = cursor.fetchall()
        conn.close()
        return logs
    
    def log_task(self, pet_id, task_type, notes=""):
        """Log completed task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO task_logs (pet_id, task_type, notes) VALUES (?, ?, ?)',
                      (pet_id, task_type, notes))
        conn.commit()
        conn.close()
    
    def get_last_task(self, pet_id, task_type):
        """Get last completion time for specific task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT completed_at FROM task_logs WHERE pet_id = ? AND task_type = ? ORDER BY completed_at DESC LIMIT 1',
                      (pet_id, task_type))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_task_streak(self, pet_id, task_type):
        """Get consecutive days of task completion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT DATE(completed_at) as task_date FROM task_logs 
                         WHERE pet_id = ? AND task_type = ? 
                         ORDER BY completed_at DESC LIMIT 30''',
                      (pet_id, task_type))
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not dates:
            return 0
        
        # Calculate streak
        from datetime import datetime, timedelta
        today = datetime.now().date()
        streak = 0
        
        for i, date_str in enumerate(dates):
            task_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            expected_date = today - timedelta(days=i)
            
            if task_date == expected_date:
                streak += 1
            else:
                break
        
        return streak
    
    def get_user_subscription(self, user_id):
        """Get user subscription status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
        subscription = cursor.fetchone()
        conn.close()
        
        if not subscription:
            # Create default free subscription
            self.create_subscription(user_id, is_premium=False)
            return {
                'is_premium': False,
                'subscription_type': 'free',
                'is_trial': False,
                'end_date': None
            }
        
        # Check if subscription is still valid
        if subscription[5]:  # end_date exists
            end_date = datetime.strptime(subscription[5], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > end_date:
                # Subscription expired, downgrade to free
                self.update_subscription(user_id, is_premium=False, subscription_type='free')
                return {
                    'is_premium': False,
                    'subscription_type': 'free',
                    'is_trial': False,
                    'end_date': None
                }
        
        return {
            'is_premium': bool(subscription[2]),
            'subscription_type': subscription[3] or 'free',
            'is_trial': bool(subscription[7]),
            'end_date': subscription[5],
            'start_date': subscription[4]
        }
    
    def create_subscription(self, user_id, is_premium=False, subscription_type='free', 
                          start_date=None, end_date=None, payment_reference=None, is_trial=False):
        """Create new subscription"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if start_date is None:
            start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT OR REPLACE INTO subscriptions 
            (user_id, is_premium, subscription_type, start_date, end_date, payment_reference, is_trial, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, is_premium, subscription_type, start_date, end_date, payment_reference, is_trial, 
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
    
    def update_subscription(self, user_id, is_premium=None, subscription_type=None, 
                          end_date=None, payment_reference=None, is_trial=None):
        """Update existing subscription"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current subscription
        cursor.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
        current = cursor.fetchone()
        
        if not current:
            # Create new subscription if doesn't exist
            self.create_subscription(user_id, is_premium or False, subscription_type or 'free')
            conn.close()
            return
        
        # Update only provided fields
        updates = []
        values = []
        
        if is_premium is not None:
            updates.append('is_premium = ?')
            values.append(is_premium)
        
        if subscription_type is not None:
            updates.append('subscription_type = ?')
            values.append(subscription_type)
        
        if end_date is not None:
            updates.append('end_date = ?')
            values.append(end_date)
        
        if payment_reference is not None:
            updates.append('payment_reference = ?')
            values.append(payment_reference)
        
        if is_trial is not None:
            updates.append('is_trial = ?')
            values.append(is_trial)
        
        updates.append('updated_at = ?')
        values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        values.append(user_id)
        
        cursor.execute(f'UPDATE subscriptions SET {", ".join(updates)} WHERE user_id = ?', values)
        conn.commit()
        conn.close()
    
    def start_trial(self, user_id):
        """Start 7-day trial for user"""
        from datetime import timedelta
        
        end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        self.create_subscription(
            user_id=user_id,
            is_premium=True,
            subscription_type='trial',
            end_date=end_date,
            is_trial=True
        )
    
    def upgrade_to_premium(self, user_id, payment_reference, duration_months=1):
        """Upgrade user to premium"""
        from datetime import timedelta
        
        end_date = (datetime.now() + timedelta(days=30 * duration_months)).strftime('%Y-%m-%d %H:%M:%S')
        self.create_subscription(
            user_id=user_id,
            is_premium=True,
            subscription_type='premium',
            end_date=end_date,
            payment_reference=payment_reference,
            is_trial=False
        )
    
    def get_ai_usage(self, user_id):
        """Get today's AI usage for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT message_count FROM ai_usage WHERE user_id = ? AND usage_date = ?', 
                      (user_id, today))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def increment_ai_usage(self, user_id):
        """Increment AI usage for today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT OR REPLACE INTO ai_usage (user_id, usage_date, message_count)
            VALUES (?, ?, COALESCE((SELECT message_count FROM ai_usage WHERE user_id = ? AND usage_date = ?), 0) + 1)
        ''', (user_id, today, user_id, today))
        
        conn.commit()
        conn.close()
    
    def store_ai_feedback(self, feedback_data):
        """Store AI feedback for improvement"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create AI feedback table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                consultation_id TEXT,
                rating INTEGER,
                detailed_feedback TEXT,
                consultation_mode TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            INSERT INTO ai_feedback (user_id, consultation_id, rating, detailed_feedback, consultation_mode, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            feedback_data['user_id'],
            feedback_data['consultation_id'], 
            feedback_data['rating'],
            feedback_data.get('detailed_feedback'),
            feedback_data.get('consultation_mode'),
            feedback_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        conn.close()
    
    def get_ai_feedback_stats(self):
        """Get AI feedback statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                AVG(rating) as avg_rating,
                COUNT(*) as total_feedback,
                consultation_mode,
                COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedback
            FROM ai_feedback 
            GROUP BY consultation_mode
        ''')
        
        stats = cursor.fetchall()
        conn.close()
        return stats
    
    def store_ai_performance(self, user_id, ai_type, performance_data):
        """Store AI performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create AI performance table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_performance (
                performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ai_type TEXT,
                consultation_id TEXT,
                tokens_used INTEGER,
                cost REAL,
                response_time REAL,
                model TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            INSERT INTO ai_performance (user_id, ai_type, consultation_id, tokens_used, cost, response_time, model, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            ai_type,
            performance_data['consultation_id'],
            performance_data['tokens_used'],
            performance_data['cost'],
            performance_data['response_time'],
            performance_data['model'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        conn.close()
    
    def get_ai_cost_report(self, period='daily'):
        """Get AI cost reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if period == 'daily':
            cursor.execute('''
                SELECT 
                    DATE(timestamp) as date,
                    SUM(cost) as total_cost,
                    SUM(tokens_used) as total_tokens,
                    COUNT(*) as total_requests,
                    ai_type,
                    model
                FROM ai_performance 
                WHERE DATE(timestamp) = DATE('now')
                GROUP BY DATE(timestamp), ai_type, model
            ''')
        elif period == 'weekly':
            cursor.execute('''
                SELECT 
                    strftime('%Y-%W', timestamp) as week,
                    SUM(cost) as total_cost,
                    SUM(tokens_used) as total_tokens,
                    COUNT(*) as total_requests,
                    ai_type,
                    model
                FROM ai_performance 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY strftime('%Y-%W', timestamp), ai_type, model
            ''')
        
        report = cursor.fetchall()
        conn.close()
        return report
    
    def log_abuse_alert(self, user_id, usage_amount, limit):
        """Log potential API abuse"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create abuse alerts table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS abuse_alerts (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                usage_amount INTEGER,
                daily_limit INTEGER,
                alert_type TEXT DEFAULT 'token_limit_exceeded',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            INSERT INTO abuse_alerts (user_id, usage_amount, daily_limit, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, usage_amount, limit, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
    
    def log_ai_insight(self, pet_id, log_date, ai_summary, extracted_tags, risk_score, model_name):
        """Log AI insight for ML training"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_insights (pet_id, log_date, ai_summary, extracted_tags, risk_score, model_name)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (pet_id, log_date, ai_summary, extracted_tags, risk_score, model_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"AI insight logging error: {e}")
            return False
    
    def log_ai_session(self, user_id, pet_id, log_date, user_message, ai_response, model_name, session_type):
        """Log complete AI chat session for ML training"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_sessions (user_id, pet_id, log_date, user_message, ai_response, model_name, session_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, pet_id, log_date, user_message, ai_response, model_name, session_type))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"AI session logging error: {e}")
            return False
    
    def get_complete_ml_dataset(self):
        """Export complete ML dataset with all joins for training"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                h.*,
                p.name as pet_name, p.species, p.breed, p.age_years, p.age_months, 
                p.weight as base_weight, p.gender, p.is_neutered, p.diseases, p.medications,
                ai.ai_summary, ai.extracted_tags, ai.risk_score, ai.model_name as insight_model,
                d.diagnosis, d.treatment, d.outcome,
                s.user_message, s.ai_response, s.model_name as session_model, s.session_type
            FROM health_logs h
            JOIN pets p ON h.pet_id = p.pet_id
            LEFT JOIN ai_insights ai ON h.pet_id = ai.pet_id AND h.log_date = ai.log_date
            LEFT JOIN diagnosis_records d ON h.pet_id = d.pet_id
            LEFT JOIN ai_sessions s ON h.pet_id = s.pet_id AND h.log_date = s.log_date
            ORDER BY h.log_date DESC
        ''')
        data = cursor.fetchall()
        conn.close()
        return data
    
    def store_ai_feedback_enhanced(self, user_id, pet_id, consultation_id, ai_type, rating, feedback_type, detailed_feedback=None):
        """Store enhanced AI feedback for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_feedback (user_id, pet_id, consultation_id, ai_type, rating, feedback_type, detailed_feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, pet_id, consultation_id, ai_type, rating, feedback_type, detailed_feedback))
        conn.commit()
        conn.close()
    
    def get_ai_learning_patterns(self, pet_id):
        """Get AI learning patterns for specific pet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ai_learning_patterns WHERE pet_id = ? ORDER BY last_updated DESC', (pet_id,))
        patterns = cursor.fetchall()
        conn.close()
        return patterns
    
    def store_ai_learning_pattern(self, pet_id, pattern_type, pattern_data, confidence_score):
        """Store AI learning pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO ai_learning_patterns (pet_id, pattern_type, pattern_data, confidence_score)
            VALUES (?, ?, ?, ?)
        ''', (pet_id, pattern_type, pattern_data, confidence_score))
        conn.commit()
        conn.close()
    
    def get_correlation_data(self, pet_id, days=30):
        """Get correlation data for diet/activity/mood analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, food_type, mood, stool_info, symptoms, weight, activity_level, notes
            FROM health_logs 
            WHERE pet_id = ? AND date >= date('now', '-{} days')
            ORDER BY date DESC
        '''.format(days), (pet_id,))
        data = cursor.fetchall()
        conn.close()
        return data
    
    def update_health_log_with_ai_analysis(self, log_id, ai_analysis, risk_factors, correlation_flags):
        """Update health log with AI analysis results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE health_logs 
            SET ai_analysis = ?, risk_factors = ?, correlation_flags = ?
            WHERE id = ?
        ''', (ai_analysis, risk_factors, correlation_flags, log_id))
        conn.commit()
        conn.close()
    
    def get_pet_historical_patterns(self, pet_id):
        """Get historical patterns for predictive analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                h.*,
                f.rating as feedback_rating,
                f.feedback_type,
                p.pattern_data,
                p.confidence_score
            FROM health_logs h
            LEFT JOIN ai_feedback f ON h.pet_id = f.pet_id AND date(h.date) = date(f.timestamp)
            LEFT JOIN ai_learning_patterns p ON h.pet_id = p.pet_id
            WHERE h.pet_id = ?
            ORDER BY h.date DESC
            LIMIT 90
        ''', (pet_id,))
        data = cursor.fetchall()
        conn.close()
        return data
    
    def save_diet_plan(self, user_id, pet_id, diet_data, generated_plan):
        """Save generated diet plan to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Mark previous plans as inactive
        cursor.execute('UPDATE diet_plans SET is_active = FALSE WHERE pet_id = ?', (pet_id,))
        
        # Insert new plan
        cursor.execute('''
            INSERT INTO diet_plans (user_id, pet_id, diet_type, goal, allergies, budget, preference, generated_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            pet_id,
            diet_data.get('diet_type', ''),
            diet_data.get('goal', ''),
            diet_data.get('allergies', ''),
            diet_data.get('budget', ''),
            diet_data.get('preference', ''),
            generated_plan
        ))
        
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return plan_id
    
    def get_pet_diet_plans(self, pet_id, limit=5):
        """Get diet plans for a pet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM diet_plans 
            WHERE pet_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (pet_id, limit))
        plans = cursor.fetchall()
        conn.close()
        return plans
    
    def get_active_diet_plan(self, pet_id):
        """Get active diet plan for a pet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM diet_plans 
            WHERE pet_id = ? AND is_active = TRUE 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (pet_id,))
        plan = cursor.fetchone()
        conn.close()
        return plan
    
    def get_user_diet_plans(self, user_id, limit=10):
        """Get all diet plans for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dp.*, p.name as pet_name, p.species 
            FROM diet_plans dp
            JOIN pets p ON dp.pet_id = p.pet_id
            WHERE dp.user_id = ? 
            ORDER BY dp.created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        plans = cursor.fetchall()
        conn.close()
        return plans

# Global database instance
db = Database()
