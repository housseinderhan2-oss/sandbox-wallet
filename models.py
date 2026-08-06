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
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_q7 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                h_1 TEXT NOT NULL, h_2 TEXT NOT NULL, h_3 TEXT NOT NULL, h_4 REAL NOT NULL,
                h_5 TEXT DEFAULT 'SUCCESS', h_6 TEXT, h_7 TEXT, h_8 TEXT
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_d2 (
                c_1 TEXT NOT NULL, c_2 TEXT NOT NULL, c_3 TEXT NOT NULL, c_4 TEXT NOT NULL, c_5 TEXT NOT NULL,
                PRIMARY KEY (c_1, c_2)
            )
            """)
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+33', '777', 'Jean Dupont', 'Lydia App France', 'France')")
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+234', '222', 'Ahmed Musa', 'OPay Nigeria', 'Nigeria')")
            conn.execute("INSERT OR IGNORE INTO tbl_d2 VALUES ('+971', '55123', 'خالد أحمد', 'محفظة e& money', 'UAE')")
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
            c_code = data["country_code"]
            p_num = data["phone_number"]
            user_msg = data.get("transfer_message", "")
            
            user_data = DatabaseManager.get_user_by_intl_phone(c_code, p_num)
            
            if user_data:
                receiver_name = user_data.get("user_name", "User")
                wallet_provider = user_data.get("wallet_provider", "System")
            else:
                receiver_name = "User" if c_code == "+234" else "Client"
                wallet_provider = data.get("target_server_name", "Global Wallet")

            fake_time = f"{random.randint(10,23)}:{random.randint(10,59)}:{random.randint(10,59)}"
            fake_date = f"2026-08-{random.randint(10,28)} {fake_time}"

            if c_code == "+33":
                top_notification = f"🔔 {wallet_provider}: Notification de crédit! {amount:,.2f} € reçus de {data['sender']}."
                statement_entry = f"Crédit: Virement {wallet_provider} reçu par {receiver_name} [+{c_code}-{p_num}]"
            elif c_code == "+234":  
                top_notification = f"🔔 {wallet_provider}: Credit alert! NGN {amount:,.2f} received from {data['sender']}."
                statement_entry = f"Credit: {wallet_provider} Transfer to {receiver_name} [+{c_code}-{p_num}]"
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
