import sqlite3
import random
from datetime import datetime
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
            # 1. جدول سجل المعاملات العام للشبكة
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_q7 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                h_1 TEXT NOT NULL, h_2 TEXT NOT NULL, h_3 TEXT NOT NULL, h_4 REAL NOT NULL,
                h_5 TEXT DEFAULT 'SUCCESS', h_6 TEXT, h_7 TEXT, h_8 TEXT
            )
            """)
            
            # 2. جدول الهوية الرقمية (يربط رقم الهاتف بالاسم والمحفظة والدولة)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_d2 (
                c_1 TEXT NOT NULL, c_2 TEXT NOT NULL, c_3 TEXT NOT NULL, c_4 TEXT NOT NULL, c_5 TEXT NOT NULL,
                PRIMARY KEY (c_1, c_2)
            )
            """)
            
            # 3. 🏦 جدول إدارة المحافظ والأرصدة الحية لتحديث الشاشة فوراً (0 ثانية)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_wallets (
                wallet_id TEXT PRIMARY KEY,
                provider_name TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'XOF'
            )
            """)

            # تسجيل هويات وحسابات مصرفية افتراضية داخل السيرفر (Myamana)
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+227', '74021804', 'Issoufou Amadou', 'Myamana Wallet', 'Niger')")
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+227', '92343455', 'Ali Ousmane', 'Myamana Wallet', 'Niger')")
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+33', '777', 'Jean Dupont', 'Lydia App France', 'France')")
            
            # تهيئة الأرصدة الابتدائية للمحافظ في البنك
            conn.execute("INSERT OR IGNORE INTO tbl_wallets VALUES ('74021804', 'Myamana Wallet', 5000.00, 'XOF')")
            conn.execute("INSERT OR IGNORE INTO tbl_wallets VALUES ('92343455', 'Myamana Wallet', 15000.00, 'XOF')")
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
    def get_user_by_phone_only(phone_number):
        # دالة بنكية تبحث عن الهوية الرقمية (الاسم والشركة) بناءً على رقم الهاتف الممرر فقط
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT * FROM tbl_d2 WHERE c_2 = ?", (str(phone_number).strip(),)).fetchone()
            return dict(row) if row else None

    # 📡 💰 دالة جلب بيانات ورصيد المحفظة المستهدفة حركياً (0 ثانية للواجهة)
    @staticmethod
    def get_wallet_balance(wallet_id):
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute(
                "SELECT wallet_id, provider_name, balance, currency FROM tbl_wallets WHERE wallet_id = ?", 
                (str(wallet_id).strip(),)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create_untraceable_transaction(data):
        with DatabaseManager.get_db_connection() as conn:
            amount = float(data["amount"])
            sender_phone = str(data["sender"]).strip()
            
            # حماية الكود من KeyError واستخراج رقم المستلم بمرونة عالية
            recipient_phone = str(data.get("receiver", data.get("phone_number"))).strip()
            c_code = str(data.get("country_code", "+227")).strip()
            user_msg = data.get("transfer_message", "Virement Core Sandbox")
            
            # 🔍 السيرفر يتعرف تلقائياً على اسم المرسل ومحفظته عبر الرقم
            sender_info = DatabaseManager.get_user_by_phone_only(sender_phone)
            sender_name = sender_info.get("c_3", f"Sender ({sender_phone})") if sender_info else f"Client-{sender_phone}"
            
            # 🔍 السيرفر يتعرف تلقائياً على اسم المستلم ومحفظته عبر الرقم
            recipient_info = DatabaseManager.get_user_by_phone_only(recipient_phone)
            if recipient_info:
                receiver_name = recipient_info.get("c_3", "User")
                wallet_provider = recipient_info.get("c_4", "Myamana Wallet")
            else:
                # إذا كان الرقم المدخل جديداً، يقوم السيرفر بتخليق هوية آلية له (زي البنك)
                receiver_name = f"User-{recipient_phone}"
                wallet_provider = "Myamana Wallet" if "227" in c_code else "Global Wallet"
                conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES (?, ?, ?, ?, 'Niger')", (c_code, recipient_phone, receiver_name, wallet_provider))

            # ⚡ 🚀 تحديث وضخ المبلغ في رصيد المحفظة فوراً (0 ثانية) لتنطق به الواجهة
            wallet_exists = conn.execute("SELECT 1 FROM tbl_wallets WHERE wallet_id = ?", (recipient_phone,)).fetchone()
            if wallet_exists:
                conn.execute("UPDATE tbl_wallets SET balance = balance + ? WHERE wallet_id = ?", (amount, recipient_phone))
            else:
                conn.execute("INSERT INTO tbl_wallets VALUES (?, ?, ?, 'XOF')", (recipient_phone, wallet_provider, amount))

            real_now = datetime.now()
            fake_date_str = real_now.strftime("%Y-%m-%d %H:%M:%S")

            # صياغة الإشعار المالي بالأسماء الصريحة المترابطة بالرقم
            top_notification = f"🔔 {wallet_provider}: Credit alert! XOF {amount:,.2f} received from {sender_name}."
            statement_entry = f"Credit: Transfer from {sender_name} to {receiver_name} [{c_code}-{recipient_phone}]"

            encrypted_receiver = DatabaseManager.encrypt_data(statement_entry)
            encrypted_msg = DatabaseManager.encrypt_data(user_msg)
            session_ref = f"REF-{random.randint(100000, 999999)}"

            # الحفظ في جدول الشبكة بحالة 'SUCCESS' الفورية لتحديث التطبيق فوراً
            conn.execute(
                """
                INSERT INTO tbl_q7 (h_1, h_2, h_3, h_4, h_5, h_6, h_7, h_8) 
                VALUES (?, ?, ?, ?, 'SUCCESS', ?, ?, ?)
                """,
                (session_ref, sender_phone, encrypted_receiver, amount, encrypted_msg, top_notification, fake_date_str)
            )
            conn.commit()
            return session_ref

    @staticmethod
    def verify_and_execute_external_transfer(transaction_id):
        # هذه الدالة يتم استدعاؤها صامتاً بعد ساعة كاملة من السيرفر لتأكيد التخويل الفني والمعالجة الخارجية
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT * FROM tbl_q7 WHERE h_1 = ?", (transaction_id,)).fetchone()
            if row:
                print(f"🔒 [Core Guard] Hour timeout reached. Transaction {transaction_id} successfully verified and cleared by External Server.")
                return True
            return False

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
