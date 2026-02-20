import os
import json
import threading
from flask import request, Blueprint
from app.models.result import Result
from app.helpers.json_util import CustomEncoder

api_bp = Blueprint("api", __name__, url_prefix="/")

# ---------------------------------------------------------------------------
# In-memory bot registry  {name -> GRIDBot or Bot instance}
# ---------------------------------------------------------------------------
_bots: dict = {}
_bot_threads: dict = {}  # {name -> Thread}


def _load_bot_from_file(name: str):
    """Try to reload a persisted bot from disk."""
    from app.bots.gridbot import GRIDBot
    from app.bots.bot import Bot
    path = f"app/bots/local/{name}.json"
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    classname = data.get("classname", "")
    if classname == "GRIDBot":
        return GRIDBot.from_json_file(path)
    return Bot.from_json_file(path)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _ping_response():
    result = Result()
    return result.to_api_response()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@api_bp.route("/api/ping", methods=["GET"])
def ping():
    """Ping."""
    try:
        return Result().to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/v", methods=["GET"])
def get_version():
    """Access version id."""
    try:
        __version__ = "v0.1.1"
        result = Result(data={"version": __version__})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/status", methods=["GET"])
def get_status():
    """Access API status."""
    try:
        result = Result(data={"api_status": "online"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


# ---------------------------------------------------------------------------
# Strategy endpoints
# ---------------------------------------------------------------------------

@api_bp.route("/api/strategy/simulate", methods=["POST"])
def simulate_strategy():
    """Simulate a trading strategy on historical data."""
    try:
        body = request.get_json(force=True, silent=True) or {}
        bot_name = body.get("name")
        if not bot_name:
            return Result(status="failed", message="'name' is required", code=400).to_api_response()

        bot = _bots.get(bot_name) or _load_bot_from_file(bot_name)
        if bot is None:
            return Result(status="failed", message=f"Bot '{bot_name}' not found", code=404).to_api_response()

        bot.simulate_trading()
        result = Result(data={"name": bot_name, "message": "Simulation completed"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/strategy/optimizations", methods=["GET"])
def get_optimized_parameters():
    """Return optimized parameters for a strategy (stub — extend with backtesting logic)."""
    try:
        result = Result(data={"message": "Optimization endpoint not yet implemented"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


# ---------------------------------------------------------------------------
# Bot CRUD endpoints
# ---------------------------------------------------------------------------

@api_bp.route("/api/bots/add", methods=["POST"])
def add_bot():
    """Register a bot by loading it from its persisted JSON file.

    Expected body: { "name": "<bot_name>" }
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        if not name:
            return Result(status="failed", message="'name' is required", code=400).to_api_response()

        if name in _bots:
            return Result(status="failed", message=f"Bot '{name}' already registered", code=409).to_api_response()

        bot = _load_bot_from_file(name)
        if bot is None:
            return Result(status="failed", message=f"No persisted state found for bot '{name}'", code=404).to_api_response()

        _bots[name] = bot
        result = Result(data={"name": name, "classname": bot.classname})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/bots/start", methods=["POST"])
def start_bot():
    """Start a registered bot in a background thread.

    Expected body: { "name": "<bot_name>" }
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        if not name:
            return Result(status="failed", message="'name' is required", code=400).to_api_response()

        bot = _bots.get(name)
        if bot is None:
            return Result(status="failed", message=f"Bot '{name}' not found. Call /api/bots/add first.", code=404).to_api_response()

        if name in _bot_threads and _bot_threads[name].is_alive():
            return Result(status="failed", message=f"Bot '{name}' is already running", code=409).to_api_response()

        def _run():
            try:
                if hasattr(bot, 'start'):
                    bot.start()
                else:
                    bot.run()
            except Exception as exc:
                print(f"[API] Bot '{name}' crashed: {exc}")

        t = threading.Thread(target=_run, daemon=True, name=f"bot-{name}")
        _bot_threads[name] = t
        t.start()

        result = Result(data={"name": name, "status": "started"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/bots/pause", methods=["POST"])
def pause_bot():
    """Pause a running bot.

    Expected body: { "name": "<bot_name>" }
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        if not name:
            return Result(status="failed", message="'name' is required", code=400).to_api_response()

        bot = _bots.get(name)
        if bot is None:
            return Result(status="failed", message=f"Bot '{name}' not found", code=404).to_api_response()

        bot.pause()
        result = Result(data={"name": name, "status": "paused"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/bots/restart", methods=["POST"])
def restart_bot():
    """Restart a bot (stop + start).

    Expected body: { "name": "<bot_name>" }
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        if not name:
            return Result(status="failed", message="'name' is required", code=400).to_api_response()

        bot = _bots.get(name)
        if bot is None:
            return Result(status="failed", message=f"Bot '{name}' not found", code=404).to_api_response()

        # Signal stop
        bot.is_running = False

        def _restart():
            try:
                if hasattr(bot, 'restart'):
                    bot.restart()
                else:
                    bot.run()
            except Exception as exc:
                print(f"[API] Bot '{name}' crashed on restart: {exc}")

        t = threading.Thread(target=_restart, daemon=True, name=f"bot-{name}-restart")
        _bot_threads[name] = t
        t.start()

        result = Result(data={"name": name, "status": "restarted"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/bots/stop", methods=["POST"])
def stop_bot():
    """Stop a running bot.

    Expected body: { "name": "<bot_name>" }
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        if not name:
            return Result(status="failed", message="'name' is required", code=400).to_api_response()

        bot = _bots.get(name)
        if bot is None:
            return Result(status="failed", message=f"Bot '{name}' not found", code=404).to_api_response()

        bot.stop()
        result = Result(data={"name": name, "status": "stopped"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/bots/update", methods=["PUT"])
def update_bot():
    """Resume a paused bot.

    Expected body: { "name": "<bot_name>" }
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        if not name:
            return Result(status="failed", message="'name' is required", code=400).to_api_response()

        bot = _bots.get(name)
        if bot is None:
            return Result(status="failed", message=f"Bot '{name}' not found", code=404).to_api_response()

        bot.update()
        result = Result(data={"name": name, "status": "updated"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/bots/<bot_name>", methods=["GET"])
def get_bot(bot_name: str):
    """Get info about a registered bot."""
    try:
        bot = _bots.get(bot_name) or _load_bot_from_file(bot_name)
        if bot is None:
            return Result(status="failed", message=f"Bot '{bot_name}' not found", code=404).to_api_response()

        thread = _bot_threads.get(bot_name)
        is_running = thread is not None and thread.is_alive()

        data = {
            "name": bot_name,
            "classname": bot.classname,
            "mode": getattr(bot, 'mode', 'unknown'),
            "pair": getattr(bot, 'pair', 'unknown'),
            "is_running": is_running,
            "runtime_s": round(bot.get_runtime(), 2) if hasattr(bot, 'get_runtime') else None,
            "realized_gain": getattr(bot, 'realized_gain', None),
        }

        result = Result(data=data)
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/bots", methods=["GET"])
def list_bots():
    """List all registered bots."""
    try:
        bot_list = []
        for name, bot in _bots.items():
            thread = _bot_threads.get(name)
            bot_list.append({
                "name": name,
                "classname": bot.classname,
                "mode": getattr(bot, 'mode', 'unknown'),
                "is_running": thread is not None and thread.is_alive(),
            })
        result = Result(data={"bots": bot_list})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()


@api_bp.route("/api/bots/remove", methods=["DELETE"])
def remove_bot():
    """Remove a bot from the registry.

    Expected body: { "name": "<bot_name>" }
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        if not name:
            return Result(status="failed", message="'name' is required", code=400).to_api_response()

        if name not in _bots:
            return Result(status="failed", message=f"Bot '{name}' not found", code=404).to_api_response()

        bot = _bots.pop(name)
        bot.is_running = False  # Signal any running thread to stop
        _bot_threads.pop(name, None)

        result = Result(data={"name": name, "status": "removed"})
        return result.to_api_response()
    except Exception as e:
        return Result(status="failed", message=f"Internal Server Error: {e}", code=500).to_api_response()
