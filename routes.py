import threading
import time
from flask import Blueprint, request, jsonify
from models import DatabaseManager

api_blueprint = Blueprint("api", __name__)

@api_blueprint.route("/admin/api/live-data", methods=["GET"])
def get_live_dashboard_data():
    # جلب كافة البيانات البنكية والحماية الموسعة
    transactions_list = DatabaseManager.get_all_transactions_for_dashboard()
    return jsonify({"status": "success", "transactions": transactions_list}), 200

@api_blueprint.route("/api/wallet/lookup/<phone_number>", methods=["GET"])
def autocomplete_target_user(phone_number):
    target = DatabaseManager.lookup_target(phone_number)
    if target:
        return jsonify({"status": "success", "found": True, "name": target["name"], "provider": target["provider"]}), 200
    return jsonify({"status": "success", "found": False}), 200

def async_reversal_timer(tx_id):
    # النوم لمدة ساعة (3600 ثانية) ثم عكس العملية برمجياً في الـ Logs وقاعدة البيانات
    time.sleep(3600)
    DatabaseManager.execute_one_hour_reversal(tx_id)

@api_blueprint.route("/api/test-transfer", methods=["POST"])
def initiate_private_transfer_simulation():
    try:
        data = request.get_json() or {}
        if "phone_number" not in data or "amount" not in data:
            return jsonify({"status": "error", "message": "Missing fields"}), 400
        
        # ضخ العملية فوراً وتوليد كافة الحقول الأربعة المطلوبة تلقائياً
        tx_id = DatabaseManager.inject_full_core_transaction(data)
        
        # إطلاق مؤقت الساعة في الخلفية لتفشل العملية لاحقاً بشكل أوتوماتيكي
        threading.Thread(target=async_reversal_timer, args=(tx_id,), daemon=True).start()
        
        return jsonify({"status": "success", "transaction_id": tx_id, "state": "SUCCESS"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
