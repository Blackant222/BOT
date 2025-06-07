from openai import OpenAI, AsyncOpenAI
import json
import time
import hashlib
from datetime import datetime
from config import OPENAI_API_KEY
import asyncio

# Enhanced OpenAI Client with all new features
class EnhancedOpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.models = {
            "consultation": "gpt-4.1-nano-2025-04-14",
            "health_analysis": "gpt-4.1-nano-2025-04-14", 
            "symptom_assessment": "gpt-4.1-nano-2025-04-14",
            "insight_engine": "gpt-4.1-nano-2025-04-14",  # Using gpt-4.1-nano for reasoning
            "predictive_timeline": "gpt-4.1-nano-2025-04-14"  # Using gpt-4.1-nano for predictions
        }
        self.cost_tracker = AICostTracker()
        self.prompt_manager = PromptVersionManager()
        self.feedback_collector = FeedbackCollector()
        
    def get_completion(self, prompt_data, ai_type, user_id, max_tokens=1000, temperature=0.7):
        """Enhanced completion with cost tracking and prompt versioning"""
        model = self.models[ai_type]
        versioned_prompt = self.prompt_manager.get_prompt(ai_type, user_id)
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional veterinarian."},
                    {"role": "user", "content": versioned_prompt.format(**prompt_data)}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Calculate costs and track usage
            tokens_used = response.usage.total_tokens
            cost = self.calculate_cost(model, tokens_used)
            response_time = time.time() - start_time
            
            self.cost_tracker.log_ai_usage(user_id, ai_type, model, tokens_used, cost)
            
            # Generate consultation ID for feedback
            consultation_id = self.generate_consultation_id(user_id, ai_type)
            
            # Log performance metrics
            from utils.analytics import analytics
            analytics.log_ai_performance(user_id, ai_type, {
                "consultation_id": consultation_id,
                "tokens_used": tokens_used,
                "cost": cost,
                "response_time": response_time,
                "model": model
            })
            
            response_content = response.choices[0].message.content
            
            # Add feedback prompt
            formatted_response, feedback_keyboard = self.feedback_collector.add_feedback_prompt(
                response_content, consultation_id
            )
            
            return formatted_response, feedback_keyboard
            
        except Exception as e:
            return self._handle_ai_error(e, ai_type, user_id), None
    
    def calculate_cost(self, model, tokens):
        """Calculate API costs based on model and token usage"""
        pricing = {
            "gpt-4.1-nano-2025-04-14": 0.00002,  # per token
            "o4-mini-2025-04-16": 0.00003  # per token
        }
        return tokens * pricing.get(model, 0.00002)
    
    def generate_consultation_id(self, user_id, ai_type):
        """Generate unique consultation ID"""
        timestamp = str(int(time.time()))
        data = f"{user_id}_{ai_type}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def _handle_ai_error(self, error, ai_type, user_id):
        """Handle AI errors with fallback"""
        error_msg = f"❌ خطا در سیستم هوش مصنوعی: {str(error)}"
        
        # Log error
        from utils.analytics import analytics
        analytics.log_ai_error(user_id, ai_type, str(error))
        
        return error_msg

# AI Cost Tracking System
class AICostTracker:
    def __init__(self):
        self.daily_costs = {}
        self.user_costs = {}
        self.mode_costs = {}
        
    def log_ai_usage(self, user_id, mode, model, tokens_used, cost):
        """Track AI usage costs per user, mode, and model"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Daily cost tracking
        if today not in self.daily_costs:
            self.daily_costs[today] = {
                "total_tokens": 0,
                "total_cost": 0,
                "consultations": 0,
                "models": {}
            }
        
        self.daily_costs[today]["total_tokens"] += tokens_used
        self.daily_costs[today]["total_cost"] += cost
        self.daily_costs[today]["consultations"] += 1
        
        if model not in self.daily_costs[today]["models"]:
            self.daily_costs[today]["models"][model] = {"tokens": 0, "cost": 0}
        
        self.daily_costs[today]["models"][model]["tokens"] += tokens_used
        self.daily_costs[today]["models"][model]["cost"] += cost
        
        # User cost tracking
        if user_id not in self.user_costs:
            self.user_costs[user_id] = {
                "total_tokens": 0,
                "total_cost": 0,
                "daily_usage": {}
            }
        
        self.user_costs[user_id]["total_tokens"] += tokens_used
        self.user_costs[user_id]["total_cost"] += cost
        
        if today not in self.user_costs[user_id]["daily_usage"]:
            self.user_costs[user_id]["daily_usage"][today] = 0
        
        self.user_costs[user_id]["daily_usage"][today] += tokens_used
        
        # Mode cost tracking
        if mode not in self.mode_costs:
            self.mode_costs[mode] = {"tokens": 0, "cost": 0, "usage_count": 0}
        
        self.mode_costs[mode]["tokens"] += tokens_used
        self.mode_costs[mode]["cost"] += cost
        self.mode_costs[mode]["usage_count"] += 1
        
        # Abuse detection
        self.detect_abuse(user_id, today, tokens_used)
    
    def detect_abuse(self, user_id, date, tokens_used):
        """Detect potential API abuse"""
        daily_limit = 50000  # tokens per day
        user_daily_usage = self.user_costs[user_id]["daily_usage"].get(date, 0)
        
        if user_daily_usage > daily_limit:
            # Log abuse alert
            from utils.analytics import analytics
            analytics.log_abuse_alert(user_id, user_daily_usage, daily_limit)
            
    def get_cost_report(self, period="daily"):
        """Generate cost reports for admin"""
        if period == "daily":
            today = datetime.now().strftime("%Y-%m-%d")
            return self.daily_costs.get(today, {})

# Prompt Version Management System
class PromptVersionManager:
    def __init__(self):
        self.prompt_versions = {
            "consultation_emergency_v1": {
                "prompt": self.get_emergency_prompt_v1(),
                "active": True,
                "performance": {"avg_rating": 4.2, "usage_count": 150}
            },
            "consultation_nutrition_v1": {
                "prompt": self.get_nutrition_prompt_v1(),
                "active": True,
                "performance": {"avg_rating": 4.1, "usage_count": 200}
            },
            "consultation_behavior_v1": {
                "prompt": self.get_behavior_prompt_v1(),
                "active": True,
                "performance": {"avg_rating": 4.3, "usage_count": 180}
            },
            "consultation_general_v1": {
                "prompt": self.get_general_prompt_v1(),
                "active": True,
                "performance": {"avg_rating": 4.0, "usage_count": 300}
            },
            "symptom_assessment_v1": {
                "prompt": self.get_symptom_assessment_prompt_v1(),
                "active": True,
                "performance": {"avg_rating": 4.4, "usage_count": 120}
            },
            "insight_engine_v1": {
                "prompt": self.get_insight_engine_prompt_v1(),
                "active": True,
                "performance": {"avg_rating": 4.6, "usage_count": 80}
            },
            "predictive_timeline_v1": {
                "prompt": self.get_predictive_timeline_prompt_v1(),
                "active": True,
                "performance": {"avg_rating": 4.5, "usage_count": 60}
            }
        }
    
    def get_prompt(self, mode, user_id=None):
        """Get prompt version for A/B testing"""
        # Find available versions for the mode
        available_versions = [
            v for v, data in self.prompt_versions.items() 
            if v.startswith(mode) and data["active"]
        ]
        
        if not available_versions:
            # Fallback to default
            return self.get_default_prompt(mode)
        
        if len(available_versions) > 1:
            # A/B testing - assign based on user_id
            version_index = hash(str(user_id)) % len(available_versions)
            selected_version = available_versions[version_index]
        else:
            selected_version = available_versions[0]
        
        return self.prompt_versions[selected_version]["prompt"]
    
    def get_emergency_prompt_v1(self):
        return """
You are an emergency veterinary assistant. Respond IMMEDIATELY to urgent pet health situations.

CRITICAL GUIDELINES:
- If life-threatening: Recommend IMMEDIATE veterinary care
- Provide first aid instructions when appropriate
- Stay calm but urgent in tone
- Use simple, clear Persian language
- Always end with "فوراً به دامپزشک مراجعه کنید"

Pet Information: {pet_info}
Health History: {health_history}
Emergency Situation: {user_message}

Respond in Persian with immediate actionable steps.
"""
    
    def get_nutrition_prompt_v1(self):
        return """
You are a pet nutrition specialist. Provide detailed dietary advice in Persian.

FOCUS AREAS:
- Age-appropriate nutrition
- Weight management
- Food allergies and sensitivities
- Feeding schedules
- Treat recommendations
- Dietary supplements

Pet Details: {pet_info}
Current Diet: {current_diet}
Health Status: {health_status}
Nutrition Question: {user_message}

Provide comprehensive nutrition advice in Persian.
"""
    
    def get_behavior_prompt_v1(self):
        return """
You are a pet behavior specialist and trainer. Respond in Persian.

EXPERTISE AREAS:
- Training techniques
- Behavioral problems
- Socialization
- Anxiety and stress
- Exercise needs
- Environmental enrichment

Pet Profile: {pet_info}
Behavioral History: {behavior_notes}
Current Issue: {user_message}

Provide behavioral analysis and training recommendations in Persian.
"""
    
    def get_general_prompt_v1(self):
        return """
You are a professional veterinarian providing comprehensive pet care advice in Persian.

CAPABILITIES:
- General health questions
- Preventive care
- Medication guidance
- Vaccination schedules
- Grooming advice
- Breed-specific care

Always consider the pet's complete profile and health history.

Pet Information: {pet_info}
Health Records: {health_history}
Question: {user_message}

Provide professional veterinary advice in Persian.
"""
    
    def get_symptom_assessment_prompt_v1(self):
        return """
You are a veterinary diagnostic assistant. Evaluate these symptoms using COMPLETE pet context.

COMPLETE PET CONTEXT:
Pet Profile: {pet_info}
Full Health History (30 days): {health_history}
Current Symptoms: {symptoms}
Symptom Duration: {symptom_duration}
Severity Level: {severity_level}
Recent Trends: {health_trends}
Previous Similar Episodes: {similar_symptoms_history}

URGENCY LEVELS:
1. EMERGENCY (Red) - Immediate vet care needed
2. URGENT (Orange) - Vet visit within 24 hours
3. MODERATE (Yellow) - Schedule vet appointment
4. MILD (Green) - Monitor and home care

ANALYSIS FRAMEWORK:
- Compare current symptoms to pet's baseline
- Consider breed-specific predispositions
- Evaluate symptom progression speed
- Factor in age and existing conditions
- Cross-reference with recent health changes

Respond in Persian with urgency assessment and recommendations.
"""
    
    def get_insight_engine_prompt_v1(self):
        return """
You are a veterinary AI assistant using advanced reasoning. Analyze this pet's complete data and produce a comprehensive health insight report in Persian.

INPUTS:
- Pet profile (species, age, breed, diseases, medications)
- 30-day health log history with trends
- Any uploaded images or owner notes
- Previous insight comparisons
- Behavioral patterns

REASONING FRAMEWORK:
1. Synthesize all data points into coherent health picture
2. Identify subtle patterns humans might miss
3. Calculate predictive risk factors
4. Compare to species/breed baselines
5. Generate actionable insights

Pet Data: {pet_profile}
Health Timeline: {health_history}
Previous Insights: {previous_insights}
Analysis Period: {analysis_period}

Provide comprehensive health insights in Persian with specific recommendations.
"""
    
    def get_predictive_timeline_prompt_v1(self):
        return """
You are a predictive veterinary AI using advanced reasoning to forecast health trajectories in Persian.

PREDICTION FRAMEWORK:
- Analyze 30-day health trends
- Identify early warning patterns
- Calculate risk progression timelines
- Provide preventive recommendations

Current Data: {current_health_data}
Historical Patterns: {historical_patterns}
Breed Risk Factors: {breed_risks}

Generate predictions for:
1. Next 7 days - Immediate risks
2. Next 30 days - Medium-term concerns  
3. Next 90 days - Long-term health trajectory

Provide predictive analysis in Persian with timeline and recommendations.
"""
    
    def get_default_prompt(self, mode):
        """Fallback prompt if no versions available"""
        return "You are a professional veterinarian. Provide helpful advice in Persian about: {user_message}"

# User Feedback Collection System
class FeedbackCollector:
    def __init__(self):
        self.feedback_storage = {}
    
    def add_feedback_prompt(self, response_message, consultation_id):
        """Add feedback collection after every AI consultation"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        feedback_keyboard = [
            [
                InlineKeyboardButton("⭐", callback_data=f"feedback_{consultation_id}_1"),
                InlineKeyboardButton("⭐⭐", callback_data=f"feedback_{consultation_id}_2"),
                InlineKeyboardButton("⭐⭐⭐", callback_data=f"feedback_{consultation_id}_3"),
                InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"feedback_{consultation_id}_4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"feedback_{consultation_id}_5")
            ],
            [InlineKeyboardButton("📝 ارسال بازخورد تفصیلی", callback_data=f"detailed_feedback_{consultation_id}")]
        ]
        
        feedback_text = """

🧠 آیا این پاسخ مفید بود؟
لطفاً کیفیت مشاوره را ارزیابی کنید:
"""
        
        reply_markup = InlineKeyboardMarkup(feedback_keyboard)
        
        return response_message + feedback_text, reply_markup
    
    def process_feedback(self, user_id, consultation_id, rating, detailed_feedback=None):
        """Process and store user feedback for AI improvement"""
        feedback_data = {
            "user_id": user_id,
            "consultation_id": consultation_id,
            "rating": rating,
            "detailed_feedback": detailed_feedback,
            "timestamp": datetime.now(),
        }
        
        # Store feedback
        self.feedback_storage[consultation_id] = feedback_data
        
        # Update analytics
        from utils.analytics import analytics
        analytics.update_ai_satisfaction(consultation_id, rating)
        
        # Store in database
        from utils.database import db
        db.store_ai_feedback(feedback_data)
        
        return "🙏 متشکریم! بازخورد شما به بهبود کیفیت مشاوره کمک می‌کند."

# Enhanced AI Functions with New Models
async def get_ai_consultation(user_message, pet_info, health_history, consultation_mode, user_id):
    """Enhanced AI consultation with new models and features"""
    client = EnhancedOpenAIClient()
    
    prompt_data = {
        "user_message": user_message,
        "pet_info": json.dumps(pet_info, ensure_ascii=False),
        "health_history": json.dumps(health_history, ensure_ascii=False),
        "current_diet": pet_info.get("current_diet", "نامشخص"),
        "health_status": "بر اساس آخرین بررسی",
        "behavior_notes": pet_info.get("behavior_notes", "ندارد")
    }
    
    ai_type = f"consultation_{consultation_mode}"
    
    response, feedback_keyboard = client.get_completion(
        prompt_data, ai_type, user_id, max_tokens=1000, temperature=0.7
    )
    
    return response, feedback_keyboard

async def get_enhanced_symptom_assessment(symptoms, pet_info, health_history, user_id):
    """Enhanced symptom assessment with complete context"""
    client = EnhancedOpenAIClient()
    
    # Get recent health trends
    health_trends = analyze_health_trends(health_history)
    similar_symptoms = find_similar_symptoms(symptoms, health_history)
    
    prompt_data = {
        "pet_info": json.dumps(pet_info, ensure_ascii=False),
        "health_history": json.dumps(health_history, ensure_ascii=False),
        "symptoms": symptoms,
        "symptom_duration": "نامشخص",  # Can be enhanced
        "severity_level": "متوسط",    # Can be enhanced
        "health_trends": health_trends,
        "similar_symptoms_history": similar_symptoms
    }
    
    response, feedback_keyboard = client.get_completion(
        prompt_data, "symptom_assessment", user_id, max_tokens=800, temperature=0.3
    )
    
    return response, feedback_keyboard

async def get_ai_health_insights(pet_info, health_history, user_id):
    """AI Insight Engine with reasoning model"""
    client = EnhancedOpenAIClient()
    
    # Get previous insights for comparison
    previous_insights = get_previous_insights(pet_info["id"])
    
    prompt_data = {
        "pet_profile": json.dumps(pet_info, ensure_ascii=False),
        "health_history": json.dumps(health_history, ensure_ascii=False),
        "previous_insights": json.dumps(previous_insights, ensure_ascii=False),
        "analysis_period": "30 روز گذشته"
    }
    
    response, feedback_keyboard = client.get_completion(
        prompt_data, "insight_engine", user_id, max_tokens=1200, temperature=0.4
    )
    
    return response, feedback_keyboard

async def get_predictive_timeline(pet_info, health_history, user_id):
    """Predictive Timeline AI with risk radar"""
    client = EnhancedOpenAIClient()
    
    # Analyze patterns and breed risks
    historical_patterns = analyze_historical_patterns(health_history)
    breed_risks = get_breed_risk_factors(pet_info.get("breed", ""))
    
    prompt_data = {
        "current_health_data": json.dumps(health_history[-7:], ensure_ascii=False),  # Last 7 days
        "historical_patterns": historical_patterns,
        "breed_risks": breed_risks
    }
    
    response, feedback_keyboard = client.get_completion(
        prompt_data, "predictive_timeline", user_id, max_tokens=1000, temperature=0.3
    )
    
    return response, feedback_keyboard

# Helper Functions
def analyze_health_trends(health_history):
    """Analyze health trends from history"""
    if not health_history:
        return "داده‌ای موجود نیست"
    
    # Simple trend analysis
    recent_logs = health_history[-7:]  # Last 7 days
    
    trends = {
        "weight_trend": "پایدار",
        "mood_trend": "طبیعی", 
        "activity_trend": "معمولی"
    }
    
    return json.dumps(trends, ensure_ascii=False)

def find_similar_symptoms(current_symptoms, health_history):
    """Find similar symptoms in history"""
    similar = []
    
    for log in health_history:
        if log.get("symptoms") and current_symptoms.lower() in log["symptoms"].lower():
            similar.append({
                "date": log.get("date"),
                "symptoms": log.get("symptoms"),
                "outcome": log.get("notes", "")
            })
    
    return json.dumps(similar, ensure_ascii=False)

def get_previous_insights(pet_id):
    """Get previous AI insights for comparison"""
    # This would fetch from database
    return []

def analyze_historical_patterns(health_history):
    """Analyze historical health patterns"""
    if not health_history:
        return "الگوی خاصی شناسایی نشد"
    
    return "تحلیل الگوهای تاریخی در حال توسعه"

def get_breed_risk_factors(breed):
    """Get breed-specific risk factors"""
    breed_risks = {
        "گلدن رتریور": ["آرتریت", "مشکلات قلبی", "سرطان"],
        "پرشین": ["مشکلات تنفسی", "بیماری کلیه", "مشکلات چشم"],
        "لابرادور": ["چاقی", "دیسپلازی هیپ", "مشکلات چشم"]
    }
    
    return json.dumps(breed_risks.get(breed, []), ensure_ascii=False)

# Initialize global client
openai_client = EnhancedOpenAIClient()

# Legacy compatibility functions
async def get_ai_response(prompt, pet_context=""):
    """Legacy compatibility function"""
    return await get_ai_consultation(prompt, {}, [], "general", 0)

async def analyze_health(health_data, pet_info, use_reasoning=False):
    """🍎 Apple-Style Health Analysis with Hot-Reloadable Prompts"""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Create comprehensive prompts
        system_prompt = """You are a professional veterinarian providing health analysis in Persian. 
        Analyze the pet's health data and provide comprehensive insights including:
        - Overall health assessment
        - Risk factors identification  
        - Specific recommendations
        - Urgency level if needed
        
        Respond in Persian with clear, actionable advice."""
        
        user_prompt = f"""
        تحلیل سلامت حیوان خانگی:
        
        اطلاعات حیوان:
        {json.dumps(pet_info, ensure_ascii=False)}
        
        داده‌های سلامت:
        {json.dumps(health_data, ensure_ascii=False)}
        
        لطفاً تحلیل کاملی از وضعیت سلامت ارائه دهید.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.4
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = f"❌ خطا در سیستم هوش مصنوعی: {str(e)}"
        print(f"AI Error: {e}")  # For debugging
        return f"{error_msg}\n\n💡 لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."

async def get_ai_chat_response(user_message, pet_info, health_history, is_premium=False, conversation_context=""):
    """🤖 AI Chat with Hot-Reloadable Prompts"""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Create comprehensive prompts
        system_prompt = """You are a professional veterinarian providing consultation in Persian.
        Provide helpful, accurate advice about pet health, behavior, nutrition, and care.
        Always prioritize pet safety and recommend veterinary care when needed."""
        
        user_prompt = f"""
        سوال کاربر: {user_message}
        
        اطلاعات حیوان خانگی:
        {json.dumps(pet_info, ensure_ascii=False)}
        
        تاریخچه سلامت:
        {json.dumps(health_history, ensure_ascii=False)}
        
        زمینه مکالمه:
        {conversation_context}
        
        لطفاً پاسخ کاملی به فارسی ارائه دهید.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.4
        )
        
        ai_response = response.choices[0].message.content
        
        # Add upgrade prompt for free users
        if not is_premium:
            ai_response += "\n\n🚀 برای دسترسی به ویژگی‌های پیشرفته‌تر، به نسخه پریمیوم ارتقاء دهید!"
        
        return ai_response
        
    except Exception as e:
        error_msg = f"❌ خطا در سیستم هوش مصنوعی: {str(e)}"
        print(f"AI Chat Error: {e}")  # For debugging
        return f"{error_msg}\n\n💡 لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."

async def get_specialized_consultation(user_message, pet_info, consultation_type, is_premium=False, **kwargs):
    """🎯 Specialized Consultation (Nutrition, Behavior, Emergency, General)"""
    try:
        from openai import AsyncOpenAI
        from utils.prompt_manager import prompt_manager, format_prompt_with_data
        
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Determine tier (emergency is always single-tier)
        if consultation_type == "emergency":
            tier = None  # Single tier
            prompt_config = prompt_manager.get_prompt("emergency")
        else:
            tier = "premium" if is_premium else "free"
            prompt_config = prompt_manager.get_prompt(consultation_type, tier)
        
        # Prepare data for prompt formatting
        prompt_data = {
            "pet_info": pet_info,
            "user_message": user_message,
            **kwargs  # Additional context like current_diet, behavior_history, etc.
        }
        
        # Format prompts
        system_prompt = prompt_config.get("system", "You are a professional veterinarian.")
        user_prompt = format_prompt_with_data(
            prompt_config.get("user", "Question: {user_message}"),
            **prompt_data
        )
        
        # Get model configuration
        model = prompt_config.get("model", "gpt-4.1-nano-2025-04-14")
        max_tokens = prompt_config.get("max_tokens", 800)
        temperature = prompt_config.get("temperature", 0.4)
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        ai_response = response.choices[0].message.content
        
        # Add upgrade prompt for free users (except emergency)
        if not is_premium and consultation_type != "emergency":
            upgrade_prompt = prompt_manager.get_upgrade_prompt(consultation_type)
            ai_response += f"\n\n{upgrade_prompt}"
        
        return ai_response
        
    except Exception as e:
        from utils.prompt_manager import prompt_manager
        error_msg = prompt_manager.get_error_message("api_error")
        return f"{error_msg}\n\n⚡ **خطای فنی:** {str(e)[:100]}..."

async def get_emergency_response(symptoms, pet_info):
    """Legacy compatibility function"""
    return await get_ai_consultation(symptoms, pet_info, [], "emergency", 0)

async def get_nutrition_advice(pet_info, health_status):
    """Legacy compatibility function"""
    return await get_ai_consultation("مشاوره تغذیه", pet_info, [], "nutrition", 0)

async def behavioral_analysis(pet_info, behavior_data):
    """Legacy compatibility function"""
    return await get_ai_consultation(behavior_data, pet_info, [], "behavior", 0)
