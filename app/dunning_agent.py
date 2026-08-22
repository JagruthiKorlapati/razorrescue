def send_dunning_message(payment_id: str, phone_number: str, upi_link: str) -> dict:
    """
    Simulated WhatsApp send. In production, this calls the WhatsApp
    Business Cloud API (POST /messages) with a template message.
    """
    message_text = (
        f"Hi! Your recent payment (ref: {payment_id}) didn't go through. "
        f"You can complete it here: {upi_link}\n\n"
        f"Reply to this message if you'd like to reschedule or have questions."
    )

    print(f"[WHATSAPP_SEND] To: {phone_number}")
    print(f"[WHATSAPP_SEND] Message: {message_text}")

    return {
        "payment_id": payment_id,
        "phone_number": phone_number,
        "message_sent": message_text,
        "status": "simulated_sent",
    }