from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import boto3
import json
import sqlite3
import os
import uuid

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Service info', service='order-service')

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
DB_PATH = os.environ.get("DB_PATH", "orders.db")

sns = boto3.client("sns", region_name=AWS_REGION)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            customer_email TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "order-service"}), 200

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    if not data or not data.get("product_name") or not data.get("customer_email"):
        return jsonify({"error": "product_name and customer_email required"}), 400

    order_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT INTO orders (id, product_name, quantity, customer_email) VALUES (?, ?, ?, ?)",
        (order_id, data["product_name"], data.get("quantity", 1), data["customer_email"])
    )
    conn.commit()
    conn.close()

    event = {
        "event_type": "order_created",
        "order_id": order_id,
        "product_name": data["product_name"],
        "quantity": data.get("quantity", 1),
        "customer_email": data["customer_email"]
    }

    if SNS_TOPIC_ARN:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(event)
        )

    return jsonify({"order_id": order_id, "message": "order created"}), 201

@app.route("/orders", methods=["GET"])
def get_orders():
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()
    return jsonify([dict(o) for o in orders]), 200

@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if order is None:
        return jsonify({"error": "order not found"}), 404
    return jsonify(dict(order)), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=False)