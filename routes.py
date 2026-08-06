from flask import Blueprint, request, jsonify, render_template
import secrets
import requests
import threading
import time
from config import Config
from models import DatabaseManager

api_blueprint = Blueprint("api", __name__)

@api_blueprint.after_request
def erase_all_network_footprints(response):
    response.headers["Server"] = "Proprietary-Core-Secure-Server/3.0"
    response.headers["X-Powered-By"] = "Unknown-Mainframe"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

@api_blueprint.route("/admin", methods=["GET"])
def admin_dashboard():
    return render_template("admin.html")

@api_blueprint.route("/admin/api/live-data", methods=["GET"])
def get_live_dashboard_data():
    try:
        token = request.headers.get("User-Agent-Validation")
        if not token or not secrets.compare_digest(token, Config.ADMIN_TOKEN):
            return jsonify({"status": "error"}), 401

        with DatabaseManager.get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM tbl_q7 ORDER BY h_8 DESC").fetchall()
            transactions_list = []
            for r in rows:
                tx = dict(r)
                transactions_list.append({
                    "id": tx["id"],
                    "app_id": tx["h_1"],
                    "receiver": DatabaseManager.decrypt_data(tx["h_3"]),
                    "amount": tx["h_4"],
                    "status": tx["h_5"],
                    "transfer_message": DatabaseManager.decrypt_data(tx["h_6"]),
                    "notification_msg": tx["h_7"],
                    "created_at": tx["h_8"]
                })
        return jsonify({"status": "success", "transactions": transactions_list}), 200
    except Exception as e:
        print(f"Log diagnostic (Hidden): {e}")
        return jsonify({"status": "error"}), 500

# 🌐 🛠️ الـ API الوهمي الجديد لمحاكاة خادم MyAmana الخارجي واستقبال التخويل
@api_blueprint.route("/api/mock-myamana/transfer", methods=["POST"])
def mock_myamana_api_server():
    try:
        # التحقق من مفتاح الأمان الممرر في طلب الـ HTTPS
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"status": "failed", "message": "Unauthorized API Key"}), 401
        
        req_data = request.get_json()
        recipient = req_data.get("recipient_wallet")
        amount = req_data.get("amount_value")
        
        # محاكاة التحقق من الحساب ووجود المستلم وتحديث الرصيد أوتوماتيكياً
        print(f"📡 [Mock MyAmana] Request Received! Processing XOF {amount} to wallet {recipient}...")
        
        # إرجاع رد نجاح قياسي يحاكي الأنظمة البنكية الحقيقية لـ MyAmana
        return jsonify({
            "status": "APPROVED",
            "transaction_id": f"AMANA-TX-{secrets.token_hex(4).upper()}",
            "cleared_balance": "Updated via Sandbox Core",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        return jsonify({"status": "SYSTEM_ERROR", "message": str(e)}), 500

# ⏳ دالة الخلفية المؤجلة المحدثة والمحمية من الأخطاء النحوية
def delayed_external_verification(tx_id, data):
    # ننتظر ساعة كاملة للتنفيذ الفعلي بناءً على خطتك
    # 💡 نصيحة: للاختبار السريع الآن يمكنك جعلها 10 ثوانٍ فقط بدلاً من 3600
    time.sleep(3600) 
    
    headers = {
        "Authorization": f"Bearer {Config.MYAMANA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "transaction_reference": tx_id,
        "sender_account": data["sender"],
        "recipient_wallet": data.get("receiver", data["phone_number"]),
        "amount_value": float(data["amount"]),
        "currency": "XOF"
    }
    
    try:
        # إرسال طلب الـ HTTPS داخلياً إلى الـ API الوهمي الذي صنعناه بالأعلى
        external_response = requests.post(Config.MYAMANA_API_URL, json=payload, headers=headers, timeout=10)
        
        if external_response.status_code in (200, 201):
            # إذا وافق الـ API الوهمي، نقوم بتحويل الحالة محلياً في الجدول إلى SUCCESS
            DatabaseManager.verify_and_execute_external_transfer(tx_id)
            print(f"⏳ Task Completed: Transaction {tx_id} verified via Mock API.")
    except Exception as e:
        print(f"⏳ Task Delayed Error: Mock API Connection issue: {e}")

@api_blueprint.route("/api/test-transfer", methods=["POST"])
def test_transfer():
    try:
        data = request.get_json()
        required = ["app_id", "sender", "country_code", "phone_number", "amount", "transfer_message"]
        if not data or not all(k in data for k in required):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
        # 1. إنشاء المعاملة بحالة PENDING لتظهر فوراً في واجهتك الحالية
        tx_id = DatabaseManager.create_untraceable_transaction(data)
        
        # 2. إطلاق المؤقت الزمني في الخلفية لطلب الـ API الوهمي بعد ساعة
        threading.Thread(target=delayed_external_verification, args=(tx_id, data), daemon=True).start()
        
        return jsonify({"status": "success", "id": tx_id, "state": "PENDING"}), 201
    except Exception as e:
        print(f"Log diagnostic (Hidden): {e}")
        return jsonify({"status": "error"}), 500
        
@api_blueprint.route("/api/transaction/<transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    try:
        transaction = DatabaseManager.get_transaction(transaction_id)
        if not transaction:
            return jsonify({"status": "error", "message": "Transaction not found"}), 404

        return jsonify({
            "status": "success",
            "transaction": {
                "id": transaction["id"],
                "app_id": transaction["session_ref"],
                "sender": transaction["sender"],
                "receiver": transaction["receiver"],
                "amount": transaction["amount"],
                "status": transaction["state"],
                "transfer_message": transaction["message"],
                "notification_msg": transaction["notification"],
                "created_at": transaction["date"]
            }
        }), 200
    except Exception as e:
        print(f"Log diagnostic (Hidden): {e}")
        return jsonify({"status": "error"}), 500
