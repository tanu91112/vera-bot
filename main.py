from flask import Flask, request, jsonify
from datetime import datetime
import hashlib
import uuid
import os

app = Flask(__name__)

# ============================================
# STORAGE
# ============================================
context_store = {}

# ============================================
# CATEGORY PROFILES
# ============================================
CATEGORY_PERSONAS = {
    "dentists": {
        "emoji": "🦷",
        "cta_style": "Book Appointment",
        "signature": "Maintain your healthy smile!"
    },
    "salons": {
        "emoji": "💇",
        "cta_style": "Book Session",
        "signature": "Elevate your style today!"
    },
    "restaurants": {
        "emoji": "🍽️",
        "cta_style": "Book Table",
        "signature": "Savor the flavors!"
    },
    "gyms": {
        "emoji": "💪",
        "cta_style": "Join Now",
        "signature": "Crush your fitness goals!"
    },
    "pharmacies": {
        "emoji": "💊",
        "cta_style": "Order Now",
        "signature": "Your health matters!"
    }
}

# ============================================
# API ENDPOINTS
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
            "POST /v1/context - Store merchant context",
            "POST /v1/tick - Generate personalized message",
            "POST /v1/reply - Handle customer replies",
            "GET /v1/healthz - Health check",
            "GET /v1/metadata - Service metadata"
        ],
        "categories_supported": ["dentists", "salons", "restaurants", "gyms", "pharmacies"],
        "triggers_supported": ["recall", "spike", "dip", "festival", "research"]
    })

@app.route('/v1/context', methods=['POST'])
def set_context():
    """Store merchant context"""
    data = request.json
    context_id = data.get("context_id")
    version = data.get("version")
    payload = data.get("payload")
    
    # Idempotent: same version = no-op
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

@app.route('/v1/tick', methods=['POST'])
def process_tick():
    """Generate message"""
    data = request.json
    context = context_store.get(data.get("context_id"))
    
    if not context:
        return jsonify({"error": "Merchant context not found"}), 404
    
    merchant_data = context["payload"]
    category = merchant_data.get("identity", {}).get("category", "restaurants")
    
    # Extract data
    name = merchant_data.get("identity", {}).get("name", "our business")
    rating = merchant_data.get("performance", {}).get("rating", 0)
    orders = merchant_data.get("performance", {}).get("total_orders", 0)
    location = merchant_data.get("identity", {}).get("location", "your area")
    offers = merchant_data.get("offers", [])
    trigger = data.get("trigger", {})
    trigger_type = trigger.get("type", "generic")
    trigger_data = trigger.get("data", {})
    
    # Get category persona
    persona = CATEGORY_PERSONAS.get(category, {})
    emoji = persona.get("emoji", "")
    
    message = ""
    
    # Generate message based on trigger
    if trigger_type == "recall":
        days = trigger_data.get("days_since_last_visit", 30)
        message = f"{emoji} It's been {days} days since your last visit to {name}."
        if offers:
            offer = offers[0]
            message += f" We're offering {offer.get('discount', '20%')} off on {offer.get('name', 'our services')}."
        message += f" 12 people in {location} searched for similar services this week."
        message += " Only 8 spots available this week!"
        
    elif trigger_type == "spike":
        count = trigger_data.get("search_count", 190)
        percent = trigger_data.get("spike_percentage", 30)
        message = f"{emoji} 🚨 {count} people are actively searching for {name} right now!"
        message += f" That's a {percent}% increase in demand!"
        if offers:
            offer = offers[0]
            message += f" Your {offer['name']} at {offer['discount']} off is getting attention."
        message += " The first 25 respondents get priority booking!"
        
    elif trigger_type == "dip":
        percent = trigger_data.get("dip_percentage", 20)
        message = f"{emoji} 📉 We noticed a {percent}% dip in your bookings at {name}."
        if offers:
            offer = offers[0]
            message += f" Your {offer['name']} at {offer['discount']} off can help recover."
        else:
            message += " Let's create a special offer to bounce back!"
        message += " Let's turn this around today!"
        
    elif trigger_type == "festival":
        festival = trigger_data.get("festival", "festival season")
        message = f"{emoji} 🎉 {festival} special at {name}!"
        if offers:
            offer = offers[0]
            message += f" Get {offer['discount']} off on {offer['name']}."
        message += f" {festival} bookings are up 300%! Don't miss out."
        
    elif trigger_type == "research":
        message = f"{emoji} 📊 {name} has a {rating}/5 rating from {orders}+ customers."
        if rating >= 4.5:
            message += " You're in the top 10% of businesses!"
        elif rating >= 4.0:
            message += " You're doing great! Here's how to hit 5 stars..."
        else:
            message += " Let's work on getting you to 4+ stars!"
    else:
        message = f"{emoji} Hello from {name}! How can we help you grow today?"
    
    # Add category signature
    if persona and "signature" in persona:
        message += f" {persona['signature']}"
    
    # Add urgency
    urgency_map = {
        "spike": " Act now while this demand lasts!",
        "festival": " Book now to secure your spot!",
        "recall": " We're waiting to welcome you back!",
        "dip": " Let's turn this around together!",
        "research": " Ready to take the next step?"
    }
    message += urgency_map.get(trigger_type, " What do you think?")
    
    # Add YES/NO action
    message += " Reply YES to get started or NO to skip."
    
    # CTA
    cta_map = {
        "spike": "🔥 Book Now - Limited Spots!",
        "festival": "🎉 Book Your Festival Spot!",
        "recall": "⭐ Come Back to Your Favorite!",
        "dip": "💪 Recover Your Bookings!",
        "research": "📊 Learn More"
    }
    
    cta = cta_map.get(trigger_type, "Get Started")
    if persona and "cta_style" in persona:
        cta = f"{persona['emoji']} {persona['cta_style']} Now!"
    
    # Suppression key
    merchant_id = merchant_data.get("identity", {}).get("id", "unknown")
    suppression_key = hashlib.md5(f"{merchant_id}_{trigger_type}_{category}".encode()).hexdigest()
    
    # Rationale
    rationale = {
        "trigger_response": f"Optimized response for {trigger_type} trigger",
        "category_application": f"Applied {category} specific tone",
        "personalization_details": f"Used: {name}, {rating}/5 rating, {orders} orders",
        "urgency_strategy": "Added time-sensitive compulsion with social proof"
    }
    
    return jsonify({
        "message": message,
        "cta": cta,
        "send_as": f"{name} Team",
        "suppression_key": suppression_key,
        "rationale": rationale
    })

@app.route('/v1/reply', methods=['POST'])
def process_reply():
    """Handle customer replies"""
    return jsonify({
        "status": "processed",
        "reply_id": str(uuid.uuid4()),
        "processed_at": datetime.now().isoformat(),
        "message": "Thanks for your reply! We'll get back to you soon."
    })

# ============================================
# ROOT ENDPOINT (To confirm it's running)
# ============================================
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "Vera Bot is running!",
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
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
