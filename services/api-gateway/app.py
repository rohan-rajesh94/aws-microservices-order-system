from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import requests
import os

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Service info', service='api-gateway')

ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service:5001")
INVENTORY_SERVICE_URL = os.environ.get("INVENTORY_SERVICE_URL", "http://inventory-service:5002")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification-service:5003")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "api-gateway"}), 200

@app.route("/api/orders", methods=["POST"])
def create_order():
    """Single entry point — client only ever talks to this gateway"""
    data = request.get_json()
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/orders", json=data, timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "order service unavailable", "details": str(e)}), 503

@app.route("/api/orders", methods=["GET"])
def get_orders():
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/orders", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "order service unavailable", "details": str(e)}), 503

@app.route("/api/stock", methods=["GET"])
def get_stock():
    try:
        response = requests.get(f"{INVENTORY_SERVICE_URL}/stock", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "inventory service unavailable", "details": str(e)}), 503

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    try:
        response = requests.get(f"{NOTIFICATION_SERVICE_URL}/notifications", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "notification service unavailable", "details": str(e)}), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)