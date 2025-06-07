# 🏗️ PetMagix Architecture Documentation

This document explains the technical architecture, design patterns, and system components of the PetMagix AI-powered pet care assistant.

## 🎯 System Overview

PetMagix is a sophisticated Telegram bot built with Python that provides AI-powered veterinary consultation and pet health management. The system uses a modular architecture with hot-reloadable AI prompts and tier-based service delivery.

## 🏛️ Core Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │   PetMagix      │    │   OpenAI        │
│   Users         │◄──►│   Bot           │◄──►│   API           │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   SQLite        │
                       │   Database      │
                       │                 │
                       └─────────────────┘
```

### Component Architecture
```
PetMagix Bot
├── 🚀 main.py (Entry Point)
├── ⚙️ config.py (Configuration)
├── 🧠 prompts.json (AI Prompts - Hot Reloadable)
├── 📁 handlers/ (Feature Modules)
│   ├── ai_chat.py (AI Consultation)
│   ├── health_analysis.py (Health Analysis)
│   ├── health_tracking.py (Daily Logging)
│   ├── pet_management.py (Pet Profiles)
│   ├── reminders.py (Automated Reminders)
│   ├── subscription.py (Tier Management)
│   └── admin_*.py (Admin Features)
├── 🛠️ utils/ (Core Utilities)
│   ├── database.py (Data Layer)
│   ├── openai_client.py (AI Integration)
│   ├── prompt_manager.py (Hot-Reload System)
│   ├── analytics.py (Usage Tracking)
│   └── keyboards.py (UI Components)
└── 📊 data/ (Persistent Storage)
    ├── petmagix.db (SQLite Database)
    └── analytics/ (Usage Data)
```

## 🔥 Hot-Reloadable Prompt System

### Design Philosophy
The prompt management system allows real-time updates to AI behavior without restarting the bot, enabling rapid iteration and A/B testing.

### Implementation Details

#### 1. Prompt Manager (`utils/prompt_manager.py`)
```python
class PromptManager:
    def __init__(self, prompts_file="prompts.json"):
        self.prompts_file = prompts_file
        self.prompts = {}
        self.last_modified = 0
        self.load_prompts()
    
    def get_prompt(self, category, tier="free"):
        # Auto-reload if file changed
        self.check_and_reload()
        return self.prompts[category][tier]
    
    def check_and_reload(self):
        # File modification detection
        current_modified = os.path.getmtime(self.prompts_file)
        if current_modified > self.last_modified:
            self.load_prompts()
            print("🔄 Prompts reloaded from prompts.json")
```

#### 2. Prompt Structure (`prompts.json`)
```json
{
  "version": "2.0",
  "prompts": {
    "health_analysis": {
      "premium": {
        "system": "Advanced veterinary AI prompt...",
        "user": "Comprehensive analysis template...",
        "model": "gpt-4.1-nano-2025-04-14",
        "max_tokens": 2000,
        "temperature": 0.2
      },
      "free": {
        "system": "Basic veterinary AI prompt...",
        "user": "Basic analysis template...",
        "model": "gpt-4.1-nano-2025-04-14",
        "max_tokens": 1000,
        "temperature": 0.4
      }
    }
  }
}
```

#### 3. Integration Pattern
```python
# In handlers
prompt_manager = PromptManager()

async def analyze_health(update, context):
    user_tier = get_user_tier(user_id)
    prompt_config = prompt_manager.get_prompt("health_analysis", user_tier)
    
    response = await openai_client.chat_completion(
        model=prompt_config["model"],
        messages=[
            {"role": "system", "content": prompt_config["system"]},
            {"role": "user", "content": prompt_config["user"].format(**data)}
        ],
        max_tokens=prompt_config["max_tokens"],
        temperature=prompt_config["temperature"]
    )
```

## 🎭 Tier-Based Service Architecture

### Service Tiers
- **Free Tier**: Basic AI consultation with limited features
- **Premium Tier**: Advanced AI analysis with comprehensive features

### Implementation
```python
def get_user_tier(user_id):
    subscription = db.get_subscription(user_id)
    return "premium" if subscription and subscription.is_active else "free"

def apply_tier_limits(user_id, feature):
    tier = get_user_tier(user_id)
    limits = TIER_LIMITS[tier][feature]
    return check_usage_against_limits(user_id, feature, limits)
```

## 🗄️ Database Architecture

### Schema Design
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    username TEXT,
    first_name TEXT,
    created_at TIMESTAMP,
    subscription_tier TEXT DEFAULT 'free'
);

-- Pets table
CREATE TABLE pets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    name TEXT,
    species TEXT,
    breed TEXT,
    age INTEGER,
    weight REAL,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Health logs table
CREATE TABLE health_logs (
    id INTEGER PRIMARY KEY,
    pet_id INTEGER,
    date DATE,
    weight REAL,
    appetite INTEGER,
    energy INTEGER,
    mood INTEGER,
    notes TEXT,
    FOREIGN KEY (pet_id) REFERENCES pets (id)
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    tier TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### Data Access Layer
```python
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    async def get_user_pets(self, user_id):
        # Async database operations
        
    async def log_health_data(self, pet_id, health_data):
        # Health logging with validation
        
    async def get_health_trends(self, pet_id, days=30):
        # Analytics and trend analysis
```

## 🤖 AI Integration Architecture

### OpenAI Client (`utils/openai_client.py`)
```python
class OpenAIClient:
    def __init__(self, api_key, model="gpt-4.1-nano-2025-04-14"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    async def chat_completion(self, messages, **kwargs):
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get('model', self.model),
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 500),
                temperature=kwargs.get('temperature', 0.3)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self.get_fallback_response()
```

### Error Handling & Fallbacks
```python
def get_fallback_response(self, category="general"):
    fallback_messages = {
        "api_error": "🔴 خطای موقت در سیستم...",
        "rate_limit": "⏰ محدودیت استفاده...",
        "invalid_input": "❌ ورودی نامعتبر..."
    }
    return fallback_messages.get(category, fallback_messages["api_error"])
```

## 📊 Analytics Architecture

### Real-time Analytics
```python
class AnalyticsManager:
    def __init__(self):
        self.daily_stats = defaultdict(int)
        self.user_actions = defaultdict(list)
    
    def track_action(self, user_id, action, metadata=None):
        timestamp = datetime.now()
        self.user_actions[user_id].append({
            "action": action,
            "timestamp": timestamp,
            "metadata": metadata
        })
        self.daily_stats[f"{action}_{timestamp.date()}"] += 1
    
    def generate_daily_report(self):
        # Generate comprehensive analytics
```

### Data Collection Points
- User interactions (commands, button clicks)
- AI consultation requests
- Health data submissions
- Error occurrences
- Performance metrics

## 🔄 Message Flow Architecture

### Request Processing Pipeline
```
User Message → Telegram API → Bot Handler → Business Logic → Database/AI → Response → User
```

### Handler Pattern
```python
# Base handler pattern
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # 1. Extract user data
        user_id = update.effective_user.id
        
        # 2. Validate permissions
        if not await validate_user_access(user_id):
            return await send_error_message(update)
        
        # 3. Process business logic
        result = await process_request(update, context)
        
        # 4. Track analytics
        analytics.track_action(user_id, "command_executed")
        
        # 5. Send response
        await send_response(update, result)
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        await send_error_message(update)
```

## 🛡️ Security Architecture

### Input Validation
```python
def validate_health_input(data):
    schema = {
        "weight": {"type": "float", "min": 0.1, "max": 200},
        "appetite": {"type": "int", "min": 1, "max": 5},
        "energy": {"type": "int", "min": 1, "max": 5}
    }
    return validate_against_schema(data, schema)
```

### Rate Limiting
```python
class RateLimiter:
    def __init__(self):
        self.user_requests = defaultdict(list)
    
    def is_allowed(self, user_id, limit=10, window=60):
        now = time.time()
        user_reqs = self.user_requests[user_id]
        
        # Clean old requests
        user_reqs[:] = [req for req in user_reqs if now - req < window]
        
        if len(user_reqs) >= limit:
            return False
        
        user_reqs.append(now)
        return True
```

## 🚀 Deployment Architecture

### Production Setup
```bash
# Process management
python main.py &

# Monitoring
tail -f logs/petmagix.log

# Health checks
curl -f http://localhost:8080/health || exit 1
```

### Scaling Considerations
- **Horizontal Scaling**: Multiple bot instances with load balancing
- **Database Scaling**: Read replicas for analytics
- **Caching**: Redis for session management
- **Monitoring**: Prometheus + Grafana for metrics

## 🔧 Configuration Management

### Environment-Based Config
```python
class Config:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.load_config()
    
    def load_config(self):
        if self.environment == 'production':
            self.load_production_config()
        else:
            self.load_development_config()
```

### Feature Flags
```python
FEATURES = {
    "premium_analytics": True,
    "ai_chat_unlimited": False,
    "experimental_features": False
}

def is_feature_enabled(feature_name, user_tier="free"):
    return FEATURES.get(feature_name, False) and (
        user_tier == "premium" or feature_name in FREE_FEATURES
    )
```

## 📈 Performance Optimization

### Async Operations
- All I/O operations are asynchronous
- Database connections pooled
- AI API calls with timeout handling
- Concurrent request processing

### Caching Strategy
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_tier(user_id):
    # Cached tier lookup
    
@lru_cache(maxsize=100)
def get_prompt_template(category, tier):
    # Cached prompt retrieval
```

## 🔍 Monitoring & Observability

### Logging Strategy
```python
import logging

# Structured logging
logger = logging.getLogger(__name__)
logger.info("User action", extra={
    "user_id": user_id,
    "action": "health_analysis",
    "tier": user_tier,
    "response_time": response_time
})
```

### Health Checks
```python
async def health_check():
    checks = {
        "database": await check_database_connection(),
        "openai": await check_openai_api(),
        "telegram": await check_telegram_api()
    }
    return all(checks.values())
```

---

This architecture provides a robust, scalable, and maintainable foundation for the PetMagix AI pet care assistant, with emphasis on real-time adaptability and user experience optimization.
