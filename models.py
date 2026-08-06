import sqlite3
import random
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
            # 1. جدول السجلات العام للحركات والشبكة
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_q7 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                h_1 TEXT NOT NULL, h_2 TEXT NOT NULL, h_3 TEXT NOT NULL, h_4 REAL NOT NULL,
                h_5 TEXT DEFAULT 'SUCCESS', h_6 TEXT, h_7 TEXT, h_8 TEXT
            )
            """)
            
            # 2. جدول بيانات المستخدمين وشركات الاتصال المستهدفة
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_d2 (
                c_1 TEXT NOT NULL, c_2 TEXT NOT NULL, c_3 TEXT NOT NULL, c_4 TEXT NOT NULL, c_5 TEXT NOT NULL,
                PRIMARY KEY (c_1, c_2)
            )
            """)
            
            # 3. 🛡️ جدول إدارة المحافظ والأرصدة الحية (أوتوماتيكي لأي تطبيق)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_wallets (
                wallet_id TEXT PRIMARY KEY,
                provider_name TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'XOF'
            )
            """)

            # إدخال البيانات الافتراضية للشبكات والمحافظ لربطها أوتوماتيكياً
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+227', '74021804', 'Myamana User', 'Myamana Wallet', 'Niger')")
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+33', '777', 'Jean Dupont', 'Lydia App France', 'France')")
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+234', '222', 'Ahmed Musa', 'OPay Nigeria', 'Nigeria')")
            
            # إنشاء حسابات المحافظ المقابلة بأرصدة تجريبية افتراضية
            conn.execute("INSERT OR IGNORE INTO tbl_wallets VALUES ('74021804', 'Myamana Wallet', 12840.00, 'XOF')")
            conn.execute("INSERT OR IGNORE INTO tbl_wallets VALUES ('777', 'Lydia App France', 2500.00, 'EUR')")
            conn.execute("INSERT OR IGNORE INTO tbl_wallets VALUES ('222', 'OPay Nigeria', 45000.00, 'NGN')")
            
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
            receiver_wallet = str(data["receiver"]).strip()
            user_msg = data.get("transfer_message", "")
            
            user_data = DatabaseManager.get_user_by_intl_phone(c_code, p_num)
            
            if user_data:
                receiver_name = user_data.get("c_3", "User")
                wallet_provider = user_data.get("c_4", "System Wallet")
            else:
                receiver_name = "Global User"
                wallet_provider = data.get("app_id", "Smart Wallet")

            # 🛠️ محرك التحديث الأوتوماتيكي للرصيد بداخل قاعدة بيانات التطبيق المستهدف
            wallet_exists = conn.execute("SELECT 1 FROM tbl_wallets WHERE wallet_id = ?", (receiver_wallet,)).fetchone()
            if wallet_exists:
                conn.execute("UPDATE tbl_wallets SET balance = balance + ? WHERE wallet_id = ?", (amount, receiver_wallet))
            else:
                # إذا لم تكن المحفظة مسجلة مسبقاً، يتم تخليقها وضخ الرصيد فيها تلقائياً ومحاكاة أي تطبيق مالي
                conn.execute("INSERT INTO tbl_wallets VALUES (?, ?, ?, 'XOF')", (receiver_wallet, wallet_provider, amount))

            fake_time = f"{random.randint(10,23)}:{random.randint(10,59)}:{random.randint(10,59)}"
            fake_date = f"2026-08-{random.randint(10,28)} {fake_time}"

            # بناء وتخصيص النصوص البرمجية لتستجيب لها واجهات التطبيقات أوتوماتيكياً بناءً على كود الدولة
            if "227" in c_code:
                top_notification = f"🔔 {wallet_provider}: Credit alert! XOF {amount:,.2f} received from {data['sender']}."
                statement_entry = f"Credit: {wallet_provider} Transfer to XOF Myamana User [{c_code}-{p_num}]"
            elif "33" in c_code:
                top_notification = f"🔔 {wallet_provider}: Notification de crédit! {amount:,.2f} € reçus de {data['sender']}."
                statement_entry = f"Crédit: Virement {wallet_provider} reçu par {receiver_name} [{c_code}-{p_num}]"
            elif "234" in c_code:  
                top_notification = f"🔔 {wallet_provider}: Credit alert! NGN {amount:,.2f} received from {data['sender']}."
                statement_entry = f"Credit: {wallet_provider} Transfer to {receiver_name} [{c_code}-{p_num}]"
            else:  
                top_notification = f"🔔 {wallet_provider}: تم استلام قيد مالي بنجاح بقيمة {amount:,.2f} د.إ من {data['sender']}."
                statement_entry = f"قيد وارد دائن: تحويل {wallet_provider} إلى {receiver_name} [{c_code}-{p_num}]"

            encrypted_receiver = DatabaseManager.encrypt_data(statement_entry)
            encrypted_msg = DatabaseManager.encrypt_data(user_msg)
            session_ref = f"REF-{random.randint(100000, 999999)}"

            conn.execute(
                """
                INSERT INTO tbl_q7 (h_1, h_2, h_3, h_4, h_5, h_6, h_7, h_8) 
                VALUES (?, ?, ?, ?, 'SUCCESS', ?, ?, ?)
                """,
                (session_ref, data["sender"], encrypted_receiver, amount, encrypted_msg, top_notification, fake_date)
            )
            conn.commit()
            return session_ref

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
