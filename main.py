from flask import Flask, request, jsonify
import hashlib
import uuid
from datetime import datetime
import os
import json

app = Flask(__name__)

# Storage
context_store = {}

# ============================================
# ROUTES
# ============================================

@app.route('/v1/healthz', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/v1/metadata', methods=['GET'])
def metadata():
    """Metadata endpoint"""
    return jsonify({
        "name": "Vera Composer - AI Challenge",
        "version": "1.0.0",
        "description": "Deterministic message composer for merchant growth",
        "endpoints": [
            "POST /v1/context",
            "POST /v1/tick",
            "POST /v1/reply",
            "GET /v1/healthz",
            "GET /v1/metadata"
        ]
    })

@app.route('/v1/context', methods=['POST'])
def set_context():
    """Store merchant context"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        context_id = data.get("context_id")
        version = data.get("version")
        payload = data.get("payload")
        
        if not context_id:
            return jsonify({"error": "Missing context_id"}), 400
        
        # Check if same version
        if context_id in context_store and context_store[context_id].get("version") == version:
            return jsonify({
                "accepted": True,
                "ack_id": str(uuid.uuid4()),
                "stored_at": datetime.now().isoformat()
            })
        
        context_store[context_id] = {
            "payload": payload,
            "version": version,
            "updated_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "accepted": True,
            "ack_id": str(uuid.uuid4()),
            "stored_at": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/tick', methods=['POST'])
def process_tick():
    """Generate message"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        context_id = data.get("context_id")
        if not context_id:
            return jsonify({"error": "Missing context_id"}), 400
            
        context = context_store.get(context_id)
        if not context:
            return jsonify({"error": "Merchant context not found"}), 404
        
        merchant_data = context["payload"]
        name = merchant_data.get("identity", {}).get("name", "our business")
        category = merchant_data.get("identity", {}).get("category", "restaurants")
        rating = merchant_data.get("performance", {}).get("rating", 0)
        orders = merchant_data.get("performance", {}).get("total_orders", 0)
        offers = merchant_data.get("offers", [])
        trigger = data.get("trigger", {})
        trigger_type = trigger.get("type", "generic")
        trigger_data = trigger.get("data", {})
        
        # Build message
        if trigger_type == "recall":
            days = trigger_data.get("days_since_last_visit", 30)
            message = f"🦷 It's been {days} days since your last visit to {name}."
        elif trigger_type == "spike":
            count = trigger_data.get("search_count", 190)
            message = f"🚨 {count} people are searching for {name} right now!"
        elif trigger_type == "dip":
            percent = trigger_data.get("dip_percentage", 20)
            message = f"📉 We noticed a {percent}% dip in your bookings."
        elif trigger_type == "festival":
            festival = trigger_data.get("festival", "festival")
            message = f"🎉 {festival} special at {name}!"
        elif trigger_type == "research":
            message = f"📊 {name} has a {rating}/5 rating from {orders}+ customers."
        else:
            message = f"Hi from {name}! How can we help you grow?"
        
        if offers:
            offer = offers[0]
            message += f" Get {offer.get('discount', '20%')} off on {offer.get('name', 'our services')}."
        
        message += " Reply YES to get started or NO to skip."
        
        return jsonify({
            "message": message,
            "cta": "Get Started",
            "send_as": f"{name} Team",
            "suppression_key": hashlib.md5(f"{context_id}_{trigger_type}".encode()).hexdigest(),
            "rationale": {
                "trigger": trigger_type,
                "category": category,
                "personalization": f"Used: {name}, {rating}/5 rating, {orders} orders",
                "urgency": "Added time-sensitive compulsion"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/reply', methods=['POST'])
def process_reply():
    """Handle customer replies"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        return jsonify({
            "status": "processed",
            "reply_id": str(uuid.uuid4()),
            "processed_at": datetime.now().isoformat(),
            "message": "Thanks for your reply! We'll get back to you soon."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Vera Bot is running!",
        "status": "healthy",
        "endpoints": [
            "/v1/healthz",
            "/v1/metadata",
            "/v1/context (POST)",
            "/v1/tick (POST)",
            "/v1/reply (POST)"
        ]
    })

# ============================================
# RUN THE APP
# ============================================

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
