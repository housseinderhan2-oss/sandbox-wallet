from flask import Blueprint, request, jsonify, render_template
import secrets
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

        # ✅ تم إصلاح الصياغة هنا وإزالة القوس الزائد
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

@api_blueprint.route("/api/test-transfer", methods=["POST"])
def test_transfer():
    try:
        data = request.get_json()
        required = ["app_id", "sender", "country_code", "phone_number", "amount", "transfer_message"]
        if not data or not all(k in data for k in required):
            return jsonify({"status": "error"}), 400
        
        tx_id = DatabaseManager.create_untraceable_transaction(data)
        return jsonify({"status": "success", "id": tx_id, "state": "SUCCESS"}), 201
    except Exception as e:
        print(f"Log diagnostic (Hidden): {e}")
        return jsonify({"status": "error"}), 500
        
# ✅ تم إصلاح محاذاة المسافات (Indentation) وإخراج الدالة خارج نطاق الدالة السابقة
@api_blueprint.route("/api/transaction/<transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    try:
        transaction = DatabaseManager.get_transaction(transaction_id)

        if not transaction:
            return jsonify({
                "status": "error",
                "message": "Transaction not found"
            }), 404

        return jsonify({
            "status": "success",
            "transaction": transaction
        }), 200
    except Exception as e:
        print(f"Log diagnostic (Hidden): {e}")
        return jsonify({"status": "error"}), 500
