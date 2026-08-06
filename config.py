import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("K_1", "change-this-secret-key-zero-day")
    ADMIN_TOKEN = os.getenv("K_2", "Mozilla_5_0_Special_Token_XMR")
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 5000))
    DATABASE_URL = "data_core.db"
 ENCRYPTION_KEY = os.getenv("K_3", "6fX5Uv9M8K2Pz7pQ4wT1xY3sN5bV8mK0L1rT4wX7zP8=").encode()

Config.MYAMANA_API_URL
Config.MYAMANA_API_KEY
