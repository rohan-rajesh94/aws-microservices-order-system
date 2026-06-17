from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import boto3
import json
import os
import threading
import time

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Service info', service='notification-service')

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@example.com")

sqs = boto3.client("sqs", region_name=AWS_REGION)
ses = boto3.client("ses", region_name=AWS_REGION)

notifications_sent = []

def send_email(to_email, product_name, quantity):
    subject = "Order Confirmation"
    body = f"Your order for {quantity}x {product_name} has been received!"

    try:
        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}}
            }
        )
        print(f"[Notification] Email sent to {to_email}")
    except Exception as e:
        print(f"[Notification] SES not configured, logging instead: {e}")

    notifications_sent.append({
        "to": to_email,
        "product": product_name,
        "quantity": quantity
    })

def poll_sqs():
    if not SQS_QUEUE_URL:
        print("[Notification] No SQS_QUEUE_URL set, skipping polling")
        return

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=10
            )
            messages = response.get("Messages", [])
            for msg in messages:
                envelope = json.loads(msg["Body"])
                body = json.loads(envelope.get("Message", envelope))
                if body.get("event_type") == "order_created":
                    send_email(
                        body["customer_email"],
                        body["product_name"],
                        body["quantity"]
                    )
                sqs.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
        except Exception as e:
            print(f"[Notification] Error polling SQS: {e}")
        time.sleep(2)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "notification-service"}), 200

@app.route("/notifications", methods=["GET"])
def get_notifications():
    return jsonify(notifications_sent), 200

if __name__ == "__main__":
    thread = threading.Thread(target=poll_sqs, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5003, debug=False)