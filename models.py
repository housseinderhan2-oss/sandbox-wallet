import sqlite3
import random
import secrets
import json
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
        """تهيئة قاعدة البيانات الشاملة لكافة حقول المرسل، المستلم، العملية، والأمان"""
        with DatabaseManager.get_db_connection() as conn:
            # 1. جدول المعاملات الموسع (يحتوي على كافة الحقول المطلوبة)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_transactions_core (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- بيانات المرسل
                sender_user_id TEXT, sender_account_id TEXT, sender_name TEXT, sender_phone TEXT, sender_auth_token TEXT,
                -- بيانات المستلم
                receiver_id TEXT, receiver_account_number TEXT, receiver_phone TEXT, receiver_provider TEXT, receiver_country TEXT,
                -- بيانات العملية
                transaction_id TEXT UNIQUE, amount REAL, currency TEXT, timestamp TEXT, status TEXT, reference TEXT,
                -- بيانات الأمان والـ Logs
                api_key_used TEXT, encryption_key_used TEXT, fraud_check_status TEXT, diagnostic_logs TEXT
            )
            """)
            
            # 2. جدول الحسابات المستهدفة الثابتة (mynita و Amana) للتعرف التلقائي
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tbl_targets_directory (
                phone TEXT PRIMARY KEY, receiver_id TEXT, account_number TEXT, name TEXT, provider TEXT, country TEXT
            )
            """)
            
            # حقن الحسابات المستهدفة المطلوبة في النيجر تلقائياً ليتعرف عليها السيستم
            conn.execute("""
                INSERT OR IGNORE INTO tbl_targets_directory VALUES 
                ('80112233', 'REC-NIT-991', 'ACC-NITA-88210', 'موسى إبراهيم', 'mynita.com', 'Niger')
            """)
            conn.execute("""
                INSERT OR IGNORE INTO tbl_targets_directory VALUES 
                ('90445566', 'REC-AMA-773', 'ACC-AMANA-55430', 'فاطمة سومانا', 'Amana Transfert', 'Niger')
            """)
            conn.commit()

    @staticmethod
    def encrypt_sensetive(text):
        return cipher.encrypt(text.encode()).decode() if text else ""

    @staticmethod
    def decrypt_sensetive(cipher_text):
        try:
            return cipher.decrypt(cipher_text.encode()).decode() if cipher_text else ""
        except Exception:
            return "Decryption Error"

    @staticmethod
    def lookup_target(phone_number):
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT * FROM tbl_targets_directory WHERE phone = ?", (str(phone_number).strip(),)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def inject_full_core_transaction(data):
        """الدالة المطلقة لضخ العملية وتخليق كافة بيانات الحماية والـ API لتجاوز القيود محلياً"""
        with DatabaseManager.get_db_connection() as conn:
            phone = str(data["phone_number"]).strip()
            amount = float(data["amount"])
            provider = data.get("selected_gateway", "mynita.com")
            
            # التعرف التلقائي على المستلم
            target = DatabaseManager.lookup_target(phone)
            if target:
                r_id = target["receiver_id"]
                r_acc = target["account_number"]
                r_name = target["name"]
                r_prov = target["provider"]
                r_country = target["country"]
            else:
                r_id = f"REC-NEW-{random.randint(100,999)}"
                r_acc = f"ACC-GEN-{random.randint(10000,99999)}"
                r_name = f"مستفيد افتراضي ({phone})"
                r_prov = provider
                r_country = "Niger"

            # توليد بيانات المرسل (تخليق تلقائي آمن كأنها قادمة من تطبيق بنكي)
            s_user_id = "USR-OWNER-777"
            s_acc_id = "ACC-CORE-MASTER"
            s_name = "المحفظة الدولية الشخصية"
            s_phone = "+227-00000000"
            s_auth_token = f"JWT_SECURE_{secrets.token_hex(16)}"

            # توليد بيانات العملية
            tx_id = f"TXN-{provider.replace('.com','').upper()}-{secrets.token_hex(4).upper()}"
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tx_ref = f"REF-{random.randint(100000, 999999)}"
            
            # توليد بيانات الأمان والـ Logs (محاكاة جدار الحماية الداخلي ليتخطى الفحص وينجح)
            mock_api_key = f"sk_live_{secrets.token_hex(12)}"
            mock_enc_key = Config.ENCRYPTION_KEY.decode()
            fraud_logs = "PROXIMITY_CHECK: PASSED | VELOCITY_LIMIT: PASSED | DEVICE_REPUTATION: TRUSTED"
            diag_logs = f"Connection opened to local sandbox core. Injecting XOF {amount} directly into DB pipeline."

            # تشفير البيانات الحساسة (مثل توكن المصادقة والبيان) لحمايتها في الداتابيز
            encrypted_auth = DatabaseManager.encrypt_sensetive(s_auth_token)
            encrypted_msg = DatabaseManager.encrypt_sensetive(data.get("transfer_message", "Instant Settled"))

            # ضخ البيانات كاملة رغماً عن أي شيء بحالة 'SUCCESS' الفورية
            conn.execute("""
                INSERT INTO tbl_transactions_core (
                    sender_user_id, sender_account_id, sender_name, sender_phone, sender_auth_token,
                    receiver_id, receiver_account_number, receiver_phone, receiver_provider, receiver_country,
                    transaction_id, amount, currency, timestamp, status, reference,
                    api_key_used, encryption_key_used, fraud_check_status, diagnostic_logs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'XOF', ?, 'SUCCESS', ?, ?, ?, ?, ?)
            """, (
                s_user_id, s_acc_id, s_name, s_phone, encrypted_auth,
                r_id, r_acc, phone, r_prov, r_country,
                tx_id, amount, current_time, tx_ref,
                mock_api_key, mock_enc_key, fraud_logs, diag_logs
            ))
            conn.commit()
            return tx_id

    @staticmethod
    def execute_one_hour_reversal(tx_id):
        """عكس العملية بعد ساعة وتحديث الـ Logs برفض المقاصة الخارجية"""
        with DatabaseManager.get_db_connection() as conn:
            row = conn.execute("SELECT * FROM tbl_transactions_core WHERE transaction_id = ?", (tx_id,)).fetchone()
            if row:
                updated_fraud = "CLEARING_HOUSE_REJECTED: External bank API keys missing or handshake timeout."
                updated_logs = "TIMEOUT: 3600s reached. Reverting visual balance injection from target wallet node."
                
                # قلب الحالة إلى FAILED وتحديث سجلات الحماية والـ Logs لتظهر أسباب الفشل
                conn.execute("""
                    UPDATE tbl_transactions_core 
                    SET status = 'FAILED', fraud_check_status = ?, diagnostic_logs = ?
                    WHERE transaction_id = ?
                """, (updated_fraud, updated_logs, tx_id))
                conn.commit()
                return True
            return False

    @staticmethod
    def get_all_transactions_for_dashboard():
        """جلب كافة الحقول الأربعة وفك تشفيرها لإطعام الواجهة بالكامل"""
        list_tx = []
        try:
            with DatabaseManager.get_db_connection() as conn:
                rows = conn.execute("SELECT * FROM tbl_transactions_core ORDER BY id DESC LIMIT 10").fetchall()
                for r in rows:
                    tx = dict(r)
                    list_tx.append({
                        "sender": {
                            "user_id": tx["sender_user_id"], "account_id": tx["sender_account_id"],
                            "name": tx["sender_name"], "phone": tx["sender_phone"]
                        },
                        "receiver": {
                            "receiver_id": tx["receiver_id"], "account_number": tx["receiver_account_number"],
                            "phone": tx["receiver_phone"], "provider": tx["receiver_provider"], "country": tx["receiver_country"]
                        },
                        "transaction": {
                            "transaction_id": tx["transaction_id"], "amount": tx["amount"], "currency": tx["currency"],
                            "timestamp": tx["timestamp"], "status": tx["status"], "reference": tx["reference"]
                        },
                        "security": {
                            "api_key": tx["api_key_used"][:12] + "...", "fraud_checks": tx["fraud_check_status"], "logs": tx["diagnostic_logs"]
                        }
                    })
        except Exception as e:
            print(e)
        return list_tx
