    @staticmethod
    def create_untraceable_transaction(data):
        with DatabaseManager.get_db_connection() as conn:
            amount = float(data["amount"])
            c_code = str(data["country_code"]).strip() # تنظيف النص من أي مسافات زائدة
            p_num = data["phone_number"]
            user_msg = data.get("transfer_message", "")
            
            user_data = DatabaseManager.get_user_by_intl_phone(c_code, p_num)
            
            if user_data:
                receiver_name = user_data.get("c_3", "User")
                wallet_provider = user_data.get("c_4", "System")
            else:
                receiver_name = "User"
                wallet_provider = data.get("target_server_name", "Myamana Wallet")

            fake_time = f"{random.randint(10,23)}:{random.randint(10,59)}:{random.randint(10,59)}"
            fake_date = f"2026-08-{random.randint(10,28)} {fake_time}"

            # 🛠️ تحسين شرط التحقق ليدعم كود النيجر بشكل صارم ومباشر ويمنع التحويل لـ NGN
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

            cursor = conn.execute(
                """
                INSERT INTO tbl_q7 (h_1, h_2, h_3, h_4, h_5, h_6, h_7, h_8) 
                VALUES (?, ?, ?, ?, 'SUCCESS', ?, ?, ?)
                """,
                (session_ref, data["sender"], encrypted_receiver, amount, encrypted_msg, top_notification, fake_date)
            )
            conn.commit()
            return session_ref
