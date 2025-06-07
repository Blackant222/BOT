import re

# Persian to English number mapping
PERSIAN_NUMBERS = {
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
}

ENGLISH_NUMBERS = {v: k for k, v in PERSIAN_NUMBERS.items()}

def persian_to_english_numbers(text):
    """Convert Persian numbers to English"""
    if not text:
        return text
    for persian, english in PERSIAN_NUMBERS.items():
        text = text.replace(persian, english)
    return text

def english_to_persian_numbers(text):
    """Convert English numbers to Persian"""
    if not text:
        return text
    for english, persian in ENGLISH_NUMBERS.items():
        text = text.replace(english, persian)
    return text

def extract_number(text):
    """Extract number from Persian/English text"""
    if not text:
        return None
    
    # Convert Persian numbers to English first
    text = persian_to_english_numbers(str(text))
    
    # Extract number using regex
    numbers = re.findall(r'\d+\.?\d*', text)
    if numbers:
        try:
            return float(numbers[0]) if '.' in numbers[0] else int(numbers[0])
        except ValueError:
            return None
    return None

def is_persian_text(text):
    """Check if text contains Persian characters"""
    if not text:
        return False
    persian_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
    return bool(persian_pattern.search(text))

def clean_persian_input(text):
    """Clean and normalize Persian input"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Convert Persian numbers to English for processing
    text = persian_to_english_numbers(text)
    
    return text

def validate_persian_name(name):
    """Validate pet name - accepts Persian, English, and numbers"""
    if not name or len(name.strip()) < 1:
        return False
    
    # Allow Persian letters, English letters, numbers, spaces, and common characters
    pattern = re.compile(r'^[\u0600-\u06FF\u0750-\u077Fa-zA-Z0-9\s\-۰-۹]+$')
    return bool(pattern.match(name.strip()))

def format_weight(weight):
    """Format weight with Persian numbers"""
    if weight is None:
        return "نامشخص"
    return f"{english_to_persian_numbers(str(weight))} کیلوگرم"

def format_age(years, months):
    """Format age in Persian"""
    if years is None and months is None:
        return "نامشخص"
    
    age_parts = []
    if years and years > 0:
        age_parts.append(f"{english_to_persian_numbers(str(years))} سال")
    if months and months > 0:
        age_parts.append(f"{english_to_persian_numbers(str(months))} ماه")
    
    return " و ".join(age_parts) if age_parts else "کمتر از یک ماه"

def persian_number(number):
    """Convert number to Persian digits"""
    return english_to_persian_numbers(str(number))

# Common Persian responses
PERSIAN_RESPONSES = {
    "yes": ["بله", "آره", "yes", "y"],
    "no": ["نه", "خیر", "no", "n"],
    "male": ["نر", "مذکر", "پسر"],
    "female": ["ماده", "مؤنث", "دختر"],
    "dog": ["سگ", "سگ‌ها"],
    "cat": ["گربه", "گربه‌ها"],
    "good": ["خوب", "عالی", "خیلی خوب"],
    "bad": ["بد", "ضعیف", "نامناسب"],
    "normal": ["عادی", "طبیعی", "معمولی"]
}

def match_persian_response(user_input, category):
    """Match user input to Persian response category"""
    if not user_input:
        return False
    
    user_input = user_input.strip().lower()
    if category in PERSIAN_RESPONSES:
        return user_input in PERSIAN_RESPONSES[category]
    return False
