import json
import os
from datetime import datetime, date, timedelta
from collections import defaultdict

class Analytics:
    def __init__(self):
        self.analytics_dir = "analytics"
        self.ensure_analytics_dir()
        
    def ensure_analytics_dir(self):
        """Create analytics directory if it doesn't exist"""
        if not os.path.exists(self.analytics_dir):
            os.makedirs(self.analytics_dir)
    
    def log_user_action(self, user_id, username, action, details=None):
        """Log user action to daily file"""
        today = date.today().isoformat()
        log_file = f"{self.analytics_dir}/user_actions_{today}.json"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "action": action,
            "details": details or {}
        }
        
        # Append to daily log file
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Analytics logging error: {e}")
    
    def log_ai_chat(self, user_id, username, message, response, is_premium=False):
        """Log AI chat interactions"""
        today = date.today().isoformat()
        chat_file = f"{self.analytics_dir}/ai_chats_{today}.json"
        
        chat_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "user_message": message,
            "ai_response": response[:200] + "..." if len(response) > 200 else response,
            "is_premium": is_premium,
            "message_length": len(message),
            "response_length": len(response)
        }
        
        try:
            if os.path.exists(chat_file):
                with open(chat_file, 'r', encoding='utf-8') as f:
                    chats = json.load(f)
            else:
                chats = []
            
            chats.append(chat_entry)
            
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(chats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Chat logging error: {e}")
    
    def log_pet_action(self, user_id, username, pet_action, pet_data=None):
        """Log pet-related actions"""
        today = date.today().isoformat()
        pet_file = f"{self.analytics_dir}/pet_actions_{today}.json"
        
        pet_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "action": pet_action,
            "pet_data": pet_data or {}
        }
        
        try:
            if os.path.exists(pet_file):
                with open(pet_file, 'r', encoding='utf-8') as f:
                    pets = json.load(f)
            else:
                pets = []
            
            pets.append(pet_entry)
            
            with open(pet_file, 'w', encoding='utf-8') as f:
                json.dump(pets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Pet logging error: {e}")
    
    def log_health_action(self, user_id, username, health_action, health_data=None):
        """Log health tracking actions"""
        today = date.today().isoformat()
        health_file = f"{self.analytics_dir}/health_actions_{today}.json"
        
        health_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "action": health_action,
            "health_data": health_data or {}
        }
        
        try:
            if os.path.exists(health_file):
                with open(health_file, 'r', encoding='utf-8') as f:
                    health = json.load(f)
            else:
                health = []
            
            health.append(health_entry)
            
            with open(health_file, 'w', encoding='utf-8') as f:
                json.dump(health, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Health logging error: {e}")
    
    def log_premium_action(self, user_id, username, premium_action, details=None):
        """Log premium/subscription actions"""
        today = date.today().isoformat()
        premium_file = f"{self.analytics_dir}/premium_actions_{today}.json"
        
        premium_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "action": premium_action,
            "details": details or {}
        }
        
        try:
            if os.path.exists(premium_file):
                with open(premium_file, 'r', encoding='utf-8') as f:
                    premium = json.load(f)
            else:
                premium = []
            
            premium.append(premium_entry)
            
            with open(premium_file, 'w', encoding='utf-8') as f:
                json.dump(premium, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Premium logging error: {e}")
    
    def generate_daily_summary(self, target_date=None):
        """Generate daily analytics summary"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        summary = {
            "date": target_date,
            "total_users": set(),
            "total_actions": 0,
            "action_breakdown": defaultdict(int),
            "ai_chats": 0,
            "pet_actions": 0,
            "health_actions": 0,
            "premium_actions": 0,
            "new_users": 0,
            "premium_users": set(),
            "most_active_users": defaultdict(int)
        }
        
        # Analyze user actions
        user_file = f"{self.analytics_dir}/user_actions_{target_date}.json"
        if os.path.exists(user_file):
            with open(user_file, 'r', encoding='utf-8') as f:
                actions = json.load(f)
                for action in actions:
                    summary["total_users"].add(action["user_id"])
                    summary["total_actions"] += 1
                    summary["action_breakdown"][action["action"]] += 1
                    summary["most_active_users"][action["user_id"]] += 1
        
        # Analyze AI chats
        chat_file = f"{self.analytics_dir}/ai_chats_{target_date}.json"
        if os.path.exists(chat_file):
            with open(chat_file, 'r', encoding='utf-8') as f:
                chats = json.load(f)
                summary["ai_chats"] = len(chats)
                for chat in chats:
                    summary["total_users"].add(chat["user_id"])
                    if chat.get("is_premium"):
                        summary["premium_users"].add(chat["user_id"])
        
        # Analyze pet actions
        pet_file = f"{self.analytics_dir}/pet_actions_{target_date}.json"
        if os.path.exists(pet_file):
            with open(pet_file, 'r', encoding='utf-8') as f:
                pets = json.load(f)
                summary["pet_actions"] = len(pets)
                for pet in pets:
                    summary["total_users"].add(pet["user_id"])
        
        # Analyze health actions
        health_file = f"{self.analytics_dir}/health_actions_{target_date}.json"
        if os.path.exists(health_file):
            with open(health_file, 'r', encoding='utf-8') as f:
                health = json.load(f)
                summary["health_actions"] = len(health)
                for h in health:
                    summary["total_users"].add(h["user_id"])
        
        # Analyze premium actions
        premium_file = f"{self.analytics_dir}/premium_actions_{target_date}.json"
        if os.path.exists(premium_file):
            with open(premium_file, 'r', encoding='utf-8') as f:
                premium = json.load(f)
                summary["premium_actions"] = len(premium)
                for p in premium:
                    summary["total_users"].add(p["user_id"])
                    if p["action"] in ["upgrade_to_premium", "start_trial"]:
                        summary["premium_users"].add(p["user_id"])
        
        # Convert sets to counts
        summary["total_users"] = len(summary["total_users"])
        summary["premium_users"] = len(summary["premium_users"])
        
        # Get top 5 most active users
        summary["top_users"] = dict(sorted(summary["most_active_users"].items(), 
                                         key=lambda x: x[1], reverse=True)[:5])
        
        # Save summary
        summary_file = f"{self.analytics_dir}/daily_summary_{target_date}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        
        return summary
    
    def get_function_popularity(self, days=7):
        """Get most popular functions over last N days"""
        function_counts = defaultdict(int)
        
        for i in range(days):
            target_date = (date.today() - timedelta(days=i)).isoformat()
            user_file = f"{self.analytics_dir}/user_actions_{target_date}.json"
            
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    actions = json.load(f)
                    for action in actions:
                        function_counts[action["action"]] += 1
        
        return dict(sorted(function_counts.items(), key=lambda x: x[1], reverse=True))
    
    def log_ai_performance(self, user_id, ai_type, performance_data):
        """Log AI performance metrics"""
        today = date.today().isoformat()
        perf_file = f"{self.analytics_dir}/ai_performance_{today}.json"
        
        perf_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "ai_type": ai_type,
            "consultation_id": performance_data.get("consultation_id"),
            "tokens_used": performance_data.get("tokens_used"),
            "cost": performance_data.get("cost"),
            "response_time": performance_data.get("response_time"),
            "model": performance_data.get("model")
        }
        
        try:
            if os.path.exists(perf_file):
                with open(perf_file, 'r', encoding='utf-8') as f:
                    perfs = json.load(f)
            else:
                perfs = []
            
            perfs.append(perf_entry)
            
            with open(perf_file, 'w', encoding='utf-8') as f:
                json.dump(perfs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"AI performance logging error: {e}")
    
    def log_ai_error(self, user_id, ai_type, error_message):
        """Log AI errors"""
        today = date.today().isoformat()
        error_file = f"{self.analytics_dir}/ai_errors_{today}.json"
        
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "ai_type": ai_type,
            "error_message": error_message
        }
        
        try:
            if os.path.exists(error_file):
                with open(error_file, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            else:
                errors = []
            
            errors.append(error_entry)
            
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"AI error logging error: {e}")
    
    def update_ai_satisfaction(self, consultation_id, rating):
        """Update AI satisfaction rating"""
        today = date.today().isoformat()
        satisfaction_file = f"{self.analytics_dir}/ai_satisfaction_{today}.json"
        
        satisfaction_entry = {
            "timestamp": datetime.now().isoformat(),
            "consultation_id": consultation_id,
            "rating": rating
        }
        
        try:
            if os.path.exists(satisfaction_file):
                with open(satisfaction_file, 'r', encoding='utf-8') as f:
                    ratings = json.load(f)
            else:
                ratings = []
            
            ratings.append(satisfaction_entry)
            
            with open(satisfaction_file, 'w', encoding='utf-8') as f:
                json.dump(ratings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"AI satisfaction logging error: {e}")
    
    def log_abuse_alert(self, user_id, usage_amount, limit):
        """Log abuse alerts"""
        today = date.today().isoformat()
        abuse_file = f"{self.analytics_dir}/abuse_alerts_{today}.json"
        
        abuse_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "usage_amount": usage_amount,
            "limit": limit,
            "alert_type": "token_limit_exceeded"
        }
        
        try:
            if os.path.exists(abuse_file):
                with open(abuse_file, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            else:
                alerts = []
            
            alerts.append(abuse_entry)
            
            with open(abuse_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Abuse alert logging error: {e}")

# Global analytics instance
analytics = Analytics()
