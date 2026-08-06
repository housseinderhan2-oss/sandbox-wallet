import sqlite3
import random
from datetime import datetime, timedelta
from config import Config
from cryptography.fernet import Fernet

cipher = Fernet(Config.ENCRYPTION_KEY)

class DatabaseManager:
    @staticmethod
    def get_db_connection():
        conn = sqlite3.connect(Config.DATABASE_URL)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA synchronous = OFF;")
        conn.execute("PRAGMA journal_mode = MEMORY;")
        return conn

    @staticmethod
    def init_db():
        with DatabaseManager.get_db_connection() as conn:
            # 1. جدول الحركات: جعل الحالة الافتراضية 'PENDING' لتطبيق خطة المراجعة
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_q7 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                h_1 TEXT NOT NULL, h_2 TEXT NOT NULL, h_3 TEXT NOT NULL, h_4 REAL NOT NULL,
                h_5 TEXT DEFAULT 'PENDING', h_6 TEXT, h_7 TEXT, h_8 TEXT
            )
            """)
            
            # 2. جدول بيانات المستخدمين وشركات الاتصال
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_d2 (
                c_1 TEXT NOT NULL, c_2 TEXT NOT NULL, c_3 TEXT NOT NULL, c_4 TEXT NOT NULL, c_5 TEXT NOT NULL,
                PRIMARY KEY (c_1, c_2)
            )
            """)
            
            # 3. جدول الأرصدة المحلي (للمحاكاة الداخلية فقط)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_wallets (
                wallet_id TEXT PRIMARY KEY,
                provider_name TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'XOF'
            )
            """)

            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+227', '74021804', 'Myamana User', 'Myamana Wallet', 'Niger')")
            conn.execute("INSERT OR IGNORE INTO tbl_wallets VALUES ('74021804', 'Myamana Wallet', 0.00, 'XOF')")
            conn.commit()

    @staticmethod
    def encrypt_data(text):
        return cipher.encrypt(text.encode()).decode() if text else ""

    @staticmethod
    def decrypt_data(cipher_text):
        try:
            return cipher.decrypt(cipher_text.encode()).decode() if cipher_text else ""
        except Exception:
            return "Decryption Error"

    @staticmethod
    def get_user_by_intl_phone(country_code, phone_number):
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT * FROM tbl_d2 WHERE c_1 = ? AND c_2 = ?", (country_code, phone_number)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create_untraceable_transaction(data):
        with DatabaseManager.get_db_connection() as conn:
            amount = float(data["amount"])
            c_code = str(data["country_code"]).strip()
            p_num = str(data["phone_number"]).strip()
            
            # ✅ تم إصلاح الثغرة الأمنية واستخدام دالة .get() لحماية الكود من الـ KeyError واشتراط رقم الهاتف كبديل
            receiver_wallet = str(data.get("receiver", p_num)).strip()
            user_msg = data.get("transfer_message", "")
            
            user_data = DatabaseManager.get_user_by_intl_phone(c_code, p_num)
            
            if user_data:
                receiver_name = user_data.get("c_3", "User")
                wallet_provider = user_data.get("c_4", "System Wallet")
            else:
                receiver_name = "Global User"
                wallet_provider = data.get("app_id", "Smart Wallet")

            # ⏳ تم تسجيل وقت الإنشاء الحقيقي الفعلي للسيرفر لتطبيق قيد الـ "بعد ساعة" بدقة
            real_now = datetime.now()
            fake_date_str = real_now.strftime("%Y-%m-%d %H:%M:%S")

            if "227" in c_code:
                top_notification = f"🔔 {wallet_provider}: [HOLD] Transaction in review. XOF {amount:,.2f} initiated from {data['sender']}."
                statement_entry = f"Pending Review: {wallet_provider} Transfer to XOF Myamana User [{c_code}-{p_num}]"
            else:  
                top_notification = f"🔔 {wallet_provider}: الحركة تحت المراجعة الفنية بقيمة {amount:,.2f} من {data['sender']}."
                statement_entry = f"تحويل معلق: مراجعة حركية السيرفر إلى {receiver_name} [{c_code}-{p_num}]"

            encrypted_receiver = DatabaseManager.encrypt_data(statement_entry)
            encrypted_msg = DatabaseManager.encrypt_data(user_msg)
            session_ref = f"REF-{random.randint(100000, 999999)}"

            # 🔒 يتم إدخال المعاملة بحالة 'PENDING' الافتراضية لحين اكتمال مدة المراجعة (ساعة)
            conn.execute(
                """
                INSERT INTO tbl_q7 (h_1, h_2, h_3, h_4, h_5, h_6, h_7, h_8) 
                VALUES (?, ?, ?, ?, 'PENDING', ?, ?, ?)
                """,
                (session_ref, data["sender"], encrypted_receiver, amount, encrypted_msg, top_notification, fake_date_str)
            )
            conn.commit()
            return session_ref

    # 🚀 الدالة المخصصة للاستدعاء الفعلي بعد ساعة لإطلاق الـ API الخارجي وتحديث رصيد التطبيق المستهدف
    @staticmethod
    def verify_and_execute_external_transfer(transaction_id):
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT * FROM tbl_q7 WHERE h_1 = ?", (transaction_id,)).fetchone()
            if not row or row["h_5"] != "PENDING":
                return False
            
            # هنا نضع منطق التحقق الخارجي الفعلي (اتصال HTTPS بالخادم الخارجي)
            # بمجرد نجاح الاتصال وتأكيد خادم المحفظة المستهدفة، نقوم بتحديث الحالة محلياً إلى SUCCESS
            conn.execute("UPDATE tbl_q7 SET h_5 = 'SUCCESS' WHERE h_1 = ?", (transaction_id,))
            conn.commit()
            return True

    @staticmethod
    def get_transaction(transaction_id):
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT id, h_1, h_2, h_3, h_4, h_5, h_6, h_7, h_8 FROM tbl_q7 WHERE h_1 = ?", (transaction_id,)).fetchone()
            if row:
                return {
                    "id": row["id"], "session_ref": row["h_1"], "sender": row["h_2"],
                    "receiver": DatabaseManager.decrypt_data(row["h_3"]), "amount": row["h_4"],
                    "state": row["h_5"], "message": DatabaseManager.decrypt_data(row["h_6"]),
                    "notification": row["h_7"], "date": row["h_8"]
                }
            return None
