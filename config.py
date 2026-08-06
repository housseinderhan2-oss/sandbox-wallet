import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("K_1", "change-this-secret-key-zero-day")
    ADMIN_TOKEN = os.getenv("K_2", "Mozilla_5_0_Special_Token_XMR")
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 5000))
    DATABASE_URL = "data_core.db"
    
    # ✅ تم إصلاح المسافات البادئة (Indentation) هنا
    ENCRYPTION_KEY = os.getenv("K_3", "6fX5Uv9M8K2Pz7pQ4wT1xY3sN5bV8mK0L1rT4wX7zP8=").encode()

    # 🔗 تم دمج وتعريف إعدادات الـ API الوهمي لـ MyAmana داخل الكلاس بشكل صحيح
    MYAMANA_API_URL = "https://onrender.com"
    MYAMANA_API_KEY = "sk_live_amana_secure_core_token_998342"
    
