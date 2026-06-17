from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import boto3
import json
import sqlite3
import os
import threading
import time

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Service info', service='inventory-service')

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
DB_PATH = os.environ.get("DB_PATH", "inventory.db")

sqs = boto3.client("sqs", region_name=AWS_REGION)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            product_name TEXT PRIMARY KEY,
            quantity_available INTEGER DEFAULT 100
        )
    """)
    conn.execute("INSERT OR IGNORE INTO stock VALUES ('shoes', 100)")
    conn.execute("INSERT OR IGNORE INTO stock VALUES ('shirt', 100)")
    conn.commit()
    conn.close()

def reduce_stock(product_name, quantity):
    conn = get_db()
    conn.execute(
        "UPDATE stock SET quantity_available = quantity_available - ? WHERE product_name = ?",
        (quantity, product_name)
    )
    conn.commit()
    conn.close()
    print(f"[Inventory] Reduced stock for {product_name} by {quantity}")

def poll_sqs():
    if not SQS_QUEUE_URL:
        print("[Inventory] No SQS_QUEUE_URL set, skipping polling")
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
                # Message arrives wrapped by SNS — actual event is inside "Message" key
                envelope = json.loads(msg["Body"])
                body = json.loads(envelope.get("Message", envelope))
                if body.get("event_type") == "order_created":
                    reduce_stock(body["product_name"], body["quantity"])
                sqs.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
        except Exception as e:
            print(f"[Inventory] Error polling SQS: {e}")
        time.sleep(2)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "inventory-service"}), 200

@app.route("/stock", methods=["GET"])
def get_stock():
    conn = get_db()
    stock = conn.execute("SELECT * FROM stock").fetchall()
    conn.close()
    return jsonify([dict(s) for s in stock]), 200

@app.route("/stock/<product_name>", methods=["GET"])
def get_product_stock(product_name):
    conn = get_db()
    item = conn.execute("SELECT * FROM stock WHERE product_name = ?", (product_name,)).fetchone()
    conn.close()
    if item is None:
        return jsonify({"error": "product not found"}), 404
    return jsonify(dict(item)), 200

if __name__ == "__main__":
    init_db()
    thread = threading.Thread(target=poll_sqs, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5002, debug=False)