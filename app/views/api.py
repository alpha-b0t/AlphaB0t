from flask import request, Blueprint
from app.models.result import Result
from app.database.data_access import *
import stripe

api_bp = Blueprint("api", __name__, url_prefix="/")

# Ping API
@api_bp.route("/api/ping", methods=["GET"])
def ping():
    """Ping."""
    try:
        result = Result()
        
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Get API version
@api_bp.route("/api/v", methods=["GET"])
def get_version():
    """Access version id."""
    try:
        __version__ = 'v0.1.1'

        result = Result(data={"version": __version__})
        
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Get API status
@api_bp.route("/api/status", methods=["GET"])
def get_status():
    """Access API status."""
    try:
        result = Result()

        result.data = {"api_status": "online"}

        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Create a Stripe Checkout Session
@api_bp.route("/api/create-checkout-session", methods=['POST'])
def create_checkout_session():
    """Creates a Stripe Checkout Session."""
    # https://stripe.com/docs/checkout/quickstart
    # https://stripe.com/docs/billing/subscriptions/build-subscriptions?ui=stripe-hosted
    try:
        # TODO: Implement
        result = Result()

        # TODO: Set stripe.api_key to Stripe API key
        checkout_session = stripe.checkout.Session.create(
            success_url='https://example.com/success.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://example.com/canceled.html',
            mode='subscription',
            line_items=[{
                'price': 'price_H5ggYwtDq4fbrJ',
                'quantity': 1
            }],
        )

        result.data = checkout_session

        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

@api_bp.route("/api/register", methods=["POST"])
def register():
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

@api_bp.route("/api/login", methods=["POST"])
def login():
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

@api_bp.route("/api/logout", methods=["POST"])
def logout():
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Get user
@api_bp.route("/api/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        result = Result()

        # TODO: Implement logic
        result.data = {"user_id": user_id}

        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Add user
@api_bp.route("/api/user/add", methods=["POST"])
def add_user():
    try:
        result = Result()

        # Fetch data from request
        data = request.get_json()

        result.data = data

        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Update user
@api_bp.route("/api/user/update", methods=["POST"])
def update_user():
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Get user's connected exchanges
@api_bp.route("/api/exchanges/<int:user_id>", methods=["GET"])
def get_user_exchanges(user_id):
    try:
        result = Result()

        result.data = {
            "user_id": user_id
        }
        
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Simulate GRID trading strategy on historical data
@api_bp.route("/api/grid-trading/simulate", methods=["POST"])
def simulate_grid_trading():
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Get genetically optimized parameters from backtesting
@api_bp.route("/api/grid-trading/optimizations", methods=["GET"])
def get_optimized_parameters():
    """Get optimized parameters for a Grid Trading Bot."""
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Add a grid trading bot
@api_bp.route("/api/grid-trading/bots/add", methods=["POST"])
def add_grid_bot():
    """Add a Grid Trading Bot."""
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Start a grid trading bot
@api_bp.route("/api/grid-trading/bots/start", methods=["POST"])
def start_grid_bot():
    """Start the Grid Trading Bot."""
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Pause a grid trading bot
@api_bp.route("/api/grid-trading/bots/pause", methods=["POST"])
def pause_grid_bot():
    """Pause the Grid Trading Bot."""
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Restart a grid trading bot
@api_bp.route("/api/grid-trading/bots/restart", methods=["POST"])
def restart_grid_bot():
    """Restart the Grid Trading Bot."""
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Stop a grid trading bot
@api_bp.route("/api/grid-trading/bots/stop", methods=["POST"])
def stop_grid_bot():
    """Stop the Grid Trading Bot."""
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Update a grid trading bot
@api_bp.route("/api/grid-trading/bots/update", methods=["PUT"])
def update_grid_bot():
    """Update the Grid Trading Bot."""
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Get a grid trading bot
@api_bp.route("/api/grid-trading/bots/<int:grid_bot_id>", methods=["GET"])
def get_grid_bot(grid_bot_id):
    """Get the Grid Trading Bot."""
    try:
        result = Result()

        # TODO: Implement logic
        result.data = {"grid_bot_id": grid_bot_id}

        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()

# Remove a grid trading bot
@api_bp.route("/api/grid-trading/bots/remove", methods=["DELETE"])
def remove_grid_bot():
    """Remove the Grid Trading Bot."""
    try:
        result = Result()
        # TODO: Implement logic
        return result.to_api_response()
    except Exception as e:
        result = Result(status="failed", message=f"Internal Server Error: {e}", code=500)
        return result.to_api_response()
