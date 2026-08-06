from flask import Blueprint, request, jsonify, render_template
import secrets
import requests
import threading  # 🚀 مكتبة إدارة العمليات الخلفية والمؤقتات الزمنية
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

# ⏳ 🤖 دالة الخلفية المؤجلة التي تم تصحيح صياغتها النحوية بدقة تامة
def delayed_external_verification(tx_id, data):
    # ننتظر ساعة كاملة قبل إرسال طلب الـ API الخارجي للمحفظة المستهدفة
    # للتجارب السريعة يمكنك تعديل الرقم من 3600 ثانية (ساعة) إلى 60 ثانية للدقيقة
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
        # إرسال التخويل الحقيقي والنهائي لتطبيق المال الخارجي وتحديث رصيد المستلم هناك
        external_response = requests.post(Config.MYAMANA_API_URL, json=payload, headers=headers, timeout=10)
        
        # ✅ تم إصلاح الصياغة النحوية واستخدام دالة التحقق المرنة والمضمونة برمجياً هنا
        if external_response.status_code in (200, 201):
            # إذا وافق السيرفر الخارجي، نقوم بتحويل الحالة محلياً إلى SUCCESS وتأكيدها
            DatabaseManager.verify_and_execute_external_transfer(tx_id)
            print(f"⏳ Task Completed: Transaction {tx_id} pushed successfully to MyAmana server.")
    except Exception as e:
        print(f"⏳ Task Delayed Error: External server communication failed: {e}")

@api_blueprint.route("/api/test-transfer", methods=["POST"])
def test_transfer():
    try:
        data = request.get_json()
        required = ["app_id", "sender", "country_code", "phone_number", "amount", "transfer_message"]
        if not data or not all(k in data for k in required):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
        # 1. إدخل المعاملة محلياً بحالة PENDING لتظهر فوراً في واجهتك الحالية كمراجعة
        tx_id = DatabaseManager.create_untraceable_transaction(data)
        
        # 2. ⚡ إطلاق المؤقت الزمني في مسار منفصل (Thread) ليعمل في خلفية السيرفر دون إيقاف التطبيق
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
