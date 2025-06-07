import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

class HotReloadablePromptManager:
    """🔥 Hot-reloadable prompt management system"""
    
    def __init__(self, prompts_file="prompts.json"):
        self.prompts_file = prompts_file
        self.prompts_data = {}
        self.last_modified = 0
        self.load_prompts()
    
    def load_prompts(self):
        """Load prompts from JSON file"""
        try:
            if os.path.exists(self.prompts_file):
                current_modified = os.path.getmtime(self.prompts_file)
                
                # Only reload if file has been modified
                if current_modified > self.last_modified:
                    with open(self.prompts_file, 'r', encoding='utf-8') as f:
                        self.prompts_data = json.load(f)
                    self.last_modified = current_modified
                    print(f"🔄 Prompts reloaded from {self.prompts_file}")
                    
        except Exception as e:
            print(f"❌ Error loading prompts: {e}")
            # Fallback to default prompts
            self.prompts_data = self.get_default_prompts()
    
    def get_prompt(self, prompt_type: str, tier: str = "free") -> Dict[str, Any]:
        """Get prompt configuration for specific type and tier"""
        # Auto-reload if file changed
        self.load_prompts()
        
        try:
            if prompt_type in self.prompts_data.get("prompts", {}):
                prompt_config = self.prompts_data["prompts"][prompt_type]
                
                # Return tier-specific prompt or fallback to general
                if tier in prompt_config:
                    return prompt_config[tier]
                elif "system" in prompt_config:  # Single-tier prompt
                    return prompt_config
                else:
                    return prompt_config.get("free", {})
            
            # Fallback to default
            return self.get_default_prompt(prompt_type, tier)
            
        except Exception as e:
            print(f"❌ Error getting prompt {prompt_type}/{tier}: {e}")
            return self.get_default_prompt(prompt_type, tier)
    
    def get_error_message(self, error_type: str) -> str:
        """Get error message"""
        self.load_prompts()
        return self.prompts_data.get("error_messages", {}).get(
            error_type, 
            "❌ خطای غیرمنتظره رخ داده است."
        )
    
    def get_upgrade_prompt(self, feature: str) -> str:
        """Get upgrade prompt for feature"""
        self.load_prompts()
        return self.prompts_data.get("upgrade_prompts", {}).get(
            feature,
            "🚀 برای دسترسی به ویژگی‌های پیشرفته، به پریمیوم ارتقاء دهید!"
        )
    
    def reload_prompts(self) -> bool:
        """Force reload prompts"""
        try:
            self.last_modified = 0  # Force reload
            self.load_prompts()
            return True
        except Exception as e:
            print(f"❌ Error reloading prompts: {e}")
            return False
    
    def get_prompt_version(self) -> str:
        """Get current prompt version"""
        self.load_prompts()
        return self.prompts_data.get("version", "1.0")
    
    def get_default_prompts(self) -> Dict[str, Any]:
        """Fallback default prompts"""
        return {
            "version": "1.0",
            "prompts": {
                "health_analysis": {
                    "free": {
                        "system": "You are a veterinarian providing basic health analysis.",
                        "user": "Analyze this pet's health: {health_data}",
                        "model": "gpt-4.1-nano-2025-04-14",
                        "max_tokens": 800,
                        "temperature": 0.4
                    }
                }
            },
            "error_messages": {
                "api_error": "❌ خطا در سیستم هوش مصنوعی"
            }
        }
    
    def get_default_prompt(self, prompt_type: str, tier: str) -> Dict[str, Any]:
        """Get default prompt configuration"""
        return {
            "system": f"You are a professional veterinarian providing {tier} tier consultation.",
            "user": "Please provide veterinary advice for: {user_message}",
            "model": "gpt-4.1-nano-2025-04-14" if tier == "free" else "o4-mini-2025-04-16",
            "max_tokens": 800 if tier == "free" else 1200,
            "temperature": 0.4
        }

# Global prompt manager instance
prompt_manager = HotReloadablePromptManager()

# Admin functions for prompt management
async def reload_prompts_command():
    """Admin command to reload prompts"""
    success = prompt_manager.reload_prompts()
    if success:
        return "✅ Prompts reloaded successfully!"
    else:
        return "❌ Failed to reload prompts."

async def get_prompt_status():
    """Get current prompt system status"""
    version = prompt_manager.get_prompt_version()
    last_modified = datetime.fromtimestamp(prompt_manager.last_modified)
    
    return f"""📋 **Prompt System Status**

🔢 **Version:** {version}
📅 **Last Updated:** {last_modified.strftime('%Y-%m-%d %H:%M:%S')}
📁 **File:** {prompt_manager.prompts_file}
🔄 **Auto-reload:** Active

💡 **Available Commands:**
• `/reload_prompts` - Force reload prompts
• `/prompt_status` - Show this status
• Edit `prompts.json` - Auto-reloads on save"""

def format_prompt_with_data(prompt_template: str, **kwargs) -> str:
    """Format prompt template with provided data"""
    try:
        return prompt_template.format(**kwargs)
    except KeyError as e:
        print(f"⚠️ Missing prompt variable: {e}")
        return prompt_template
    except Exception as e:
        print(f"❌ Error formatting prompt: {e}")
        return prompt_template
