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
        """تهيئة قاعدة البيانات الخاصة بالمشروع الشخصي وضخ الحسابين المستهدفين في النيجر."""
        with DatabaseManager.get_db_connection() as conn:
            # 1. جدول الحركات المالية المسجلة
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_q7 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                h_1 TEXT NOT NULL, h_2 TEXT NOT NULL, h_3 TEXT NOT NULL, h_4 REAL NOT NULL,
                h_5 TEXT DEFAULT 'SUCCESS', h_6 TEXT, h_7 TEXT, h_8 TEXT
            )
            """)
            
            # 2. جدول الهويات (الحسابين المستهدفين في النيجر بشكل دائم)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_d2 (
                c_1 TEXT NOT NULL, c_2 TEXT NOT NULL, c_3 TEXT NOT NULL, c_4 TEXT NOT NULL, c_5 TEXT NOT NULL,
                PRIMARY KEY (c_1, c_2)
            )
            """)
            
            # 3. جدول الأرصدة الظاهرة على الشاشة لإبراز المبلغ فوراً
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_wallets (
                wallet_id TEXT PRIMARY KEY,
                provider_name TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'XOF'
            )
            """)

            # حقن الحسابين المستهدفين حصرياً في النيجر (الاستخدام الشخصي)
            # المحفظة الأولى (مثال: محفظة أمانة النيجر)
            conn.execute("""
                INSERT OR IGNORE INTO tbl_d2 VALUES 
                ('+227', '80112233', 'موسى إبراهيم (الحساب المستهدف A)', 'MyAmana Niger', 'Niger')
            """)
            # المحفظة الثانية (مثال: محفظة النيجر الثانية المحدثة)
            conn.execute("""
                INSERT OR IGNORE INTO tbl_d2 VALUES 
                ('+227', '90445566', 'فاطمة سومانا (الحساب المستهدف B)', 'Aliza Wallet Niger', 'Niger')
            """)
            
            # تهيئة أرصدة ابتدائية وهمية لعرضها في الشاشة
            conn.execute("INSERT OR IGNORE INTO tbl_wallets VALUES ('80112233', 'MyAmana Niger', 1000.00, 'XOF')")
            conn.execute("INSERT OR IGNORE INTO tbl_wallets VALUES ('90445566', 'Aliza Wallet Niger', 2500.00, 'XOF')")
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
    def get_target_user_by_phone(phone_number):
        """التعرف التلقائي الفوري على اسم المستهدف بمجرد إدخال رقمه (مثل البنك)"""
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT * FROM tbl_d2 WHERE c_2 = ?", (str(phone_number).strip(),)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_wallet_balance(wallet_id):
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT * FROM tbl_wallets WHERE wallet_id = ?", (str(wallet_id).strip(),)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create_instant_simulation_transfer(data):
        """ضخ المبلغ في حساب الشخص فوراً وبحالة SUCCESS فورية 100% ليظهر المبلغ في الشاشة"""
        with DatabaseManager.get_db_connection() as conn:
            amount = float(data["amount"])
            recipient_phone = str(data["phone_number"]).strip()
            sender_name = "المحفظة الدولية الموثوقة"
            user_msg = data.get("transfer_message", "حوالة فورية مسواة")
            
            # استخراج الهوية تلقائياً بناءً على الرقم المستهدف
            target_info = DatabaseManager.get_target_user_by_phone(recipient_phone)
            if target_info:
                receiver_name = target_info["c_3"]
                wallet_provider = target_info["c_4"]
            else:
                receiver_name = f"حساب غير مسجل ({recipient_phone})"
                wallet_provider = "MyAmana Niger"

            # ⚡ تحديث وضخ المبلغ في رصيد محفظة المستهدف فوراً ليقرأه المتصفح
            wallet_exists = conn.execute("SELECT 1 FROM tbl_wallets WHERE wallet_id = ?", (recipient_phone,)).fetchone()
            if wallet_exists:
                conn.execute("UPDATE tbl_wallets SET balance = balance + ? WHERE wallet_id = ?", (amount, recipient_phone))
            else:
                conn.execute("INSERT INTO tbl_wallets VALUES (?, ?, ?, 'XOF')", (recipient_phone, wallet_provider, amount))

            fake_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # صياغة الإشعار المالي الذي يظهر أعلى شاشة المحفظة
            top_notification = f"🔔 {wallet_provider}: تم استقبال مبلغ XOF {amount:,.2f} بنجاح من {sender_name}."
            statement_entry = f"Credit: تحويل بنكي مباشر إلى {receiver_name} [{recipient_phone}]"

            encrypted_receiver = DatabaseManager.encrypt_data(statement_entry)
            encrypted_msg = DatabaseManager.encrypt_data(user_msg)
            session_ref = f"TX-NER-{random.randint(100000, 999999)}"

            # التسجيل المبدئي في الشبكة بحالة 'SUCCESS' الفورية لتحديث الشاشة
            conn.execute("""
                INSERT INTO tbl_q7 (h_1, h_2, h_3, h_4, h_5, h_6, h_7, h_8) 
                VALUES (?, ?, ?, ?, 'SUCCESS', ?, ?, ?)
            """, (session_ref, "SYSTEM_OWNER", encrypted_receiver, amount, encrypted_msg, top_notification, fake_date_str))
            
            conn.commit()
            return session_ref

    @staticmethod
    def trigger_hourly_reversal_failure(transaction_id):
        """
        ⚡ سر الخدعة والمحاكاة: هذه الدالة تستدعى في الخلفية بعد ساعة كاملة
        لتحويل حالة المعاملة إلى فشل (FAILED) وسحب المبلغ من رصيد الشاشة المستهدفة.
        """
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT h_4, h_3 FROM tbl_q7 WHERE h_1 = ?", (transaction_id,)).fetchone()
            if row:
                amount = row["h_4"]
                decrypted_receiver = DatabaseManager.decrypt_data(row["h_3"])
                
                # استخراج رقم هاتف المستهدف من حقل النص لخصم الرصيد منه
                recipient_phone = "80112233"
                if '[' in decrypted_receiver:
                    recipient_phone = decrypted_receiver.split('[')[-1].split(']')[0]

                # 1. قلب حالة المعاملة إلى فشل تام FAILED في كشف الحساب
                conn.execute("UPDATE tbl_q7 SET h_5 = 'FAILED' WHERE h_1 = ?", (transaction_id,))
                
                # 2. خصم المبلغ الذي تم ضخه من محفظة المستهدف (إلغاء أثر الرصيد من الواجهة)
                conn.execute("UPDATE tbl_wallets SET balance = MAX(0.0, balance - ?) WHERE wallet_id = ?", (amount, recipient_phone))
                
                # 3. تحديث رسالة الإشعار لتظهر للمستخدم أن السيرفر الحقيقي رفض المعاملة
                fail_notif = f"❌ رفض نظام المقاصة: فشل التحقق الخارجي للعملية {transaction_id}. تم إلغاء تخصيص الأموال."
                conn.execute("UPDATE tbl_q7 SET h_7 = ? WHERE h_1 = ?", (fail_notif, transaction_id))
                
                conn.commit()
                print(f"🔒 [Reversal Core] Hour timeout reached. Simulation flipped to FAILED for {transaction_id}.")
                return True
            return False

    @staticmethod
    def get_all_transactions_for_api():
        transactions_list = []
        try:
            with DatabaseManager.get_db_connection() as conn:
                rows = conn.execute("SELECT h_1, h_2, h_3, h_4, h_5, h_6, h_7, h_8 FROM tbl_q7 ORDER BY id DESC LIMIT 10").fetchall()
                for row in rows:
                    transactions_list.append({
                        "app_id": row["h_1"],
                        "receiver": DatabaseManager.decrypt_data(row["h_3"]),
                        "created_at": row["h_8"],
                        "transfer_message": DatabaseManager.decrypt_data(row["h_6"]),
                        "amount": float(row["h_4"]),
                        "status": row["h_5"],  # ستكون SUCCESS وتتحول تلقائياً إلى FAILED بعد ساعة
                        "notification_msg": row["h_7"]
                    })
        except Exception as e:
            print(f"Error: {e}")
        return transactions_list
