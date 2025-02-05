from flask import Flask, render_template, jsonify, request
import requests
import os
import datetime

# Flask-Limiter for rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Flask-Caching for caching endpoints
from flask_caching import Cache

# Flask-SQLAlchemy for database logging
from flask_sqlalchemy import SQLAlchemy

# APScheduler for background jobs
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# -----------------------
# Configuration
# -----------------------

# Rate Limiter configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]  # 100 requests per hour per IP
)
limiter.init_app(app)

# Caching configuration (in-memory cache, 10 minutes timeout)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# Database configuration (using SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -----------------------
# Models
# -----------------------

# Model for logging currency data (for historical tracking)
class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    usd_to_cad = db.Column(db.Float, nullable=False)
    usd_to_mxn = db.Column(db.Float, nullable=False)
    usd_to_cny = db.Column(db.Float, nullable=False)
    usd_to_jpy = db.Column(db.Float, nullable=False)
    bitcoin_price = db.Column(db.Float, nullable=False)

# Model for Flappy Bird high scores (if needed; not used if game is removed)
class FlappyScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

with app.app_context():
    db.create_all()

# -----------------------
# External API Configuration
# -----------------------
CURRENCY_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
if not NEWS_API_KEY:
    raise ValueError("No NEWS_API_KEY set for Flask application")
NEWS_API_URL = "https://newsapi.org/v2/everything"

# -----------------------
# Helper Functions
# -----------------------
def get_bitcoin_price():
    """Fetch current Bitcoin price (USD) from CoinDesk API."""
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
        data = response.json()
        return data["bpi"]["USD"]["rate_float"]
    except Exception:
        return 0

def log_currency_data():
    """
    Fetch current exchange rates (USD vs. CAD, MXN, CNY, JPY) and Bitcoin price,
    then log them to the database.
    """
    try:
        response = requests.get(CURRENCY_API_URL)
        data = response.json()
        usd_to_cad = data.get("rates", {}).get("CAD")
        usd_to_mxn = data.get("rates", {}).get("MXN")
        usd_to_cny = data.get("rates", {}).get("CNY")
        usd_to_jpy = data.get("rates", {}).get("JPY")
        bitcoin_price = get_bitcoin_price()

        new_log = LogEntry(
            usd_to_cad=usd_to_cad,
            usd_to_mxn=usd_to_mxn,
            usd_to_cny=usd_to_cny,
            usd_to_jpy=usd_to_jpy,
            bitcoin_price=bitcoin_price
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        print("Error logging currency data:", e)

# -----------------------
# APScheduler: Periodic Data Logging
# -----------------------
scheduler = BackgroundScheduler()
scheduler.add_job(func=log_currency_data, trigger="interval", minutes=10)
scheduler.start()

# -----------------------
# Routes: USD Tracking & Analysis
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/currency-data")
@limiter.limit("50 per hour")
@cache.cached()  # Cache current data for 10 minutes
def currency_data():
    """
    Fetch current exchange rates for USD vs. CAD, MXN, CNY, and JPY,
    along with the current Bitcoin price.
    Generate a 3-day sample (with slight random variations for demonstration).
    (Note: The scheduled job is logging real data periodically.)
    """
    try:
        response = requests.get(CURRENCY_API_URL)
        data = response.json()
        usd_to_cad = data.get("rates", {}).get("CAD")
        usd_to_mxn = data.get("rates", {}).get("MXN")
        usd_to_cny = data.get("rates", {}).get("CNY")
        usd_to_jpy = data.get("rates", {}).get("JPY")
        bitcoin_price = get_bitcoin_price()

        # Generate a 3-day sample (for display purposes only)
        import random
        cad_history = [
            round(usd_to_cad - random.uniform(0, 0.02), 4),
            round(usd_to_cad - random.uniform(0, 0.01), 4),
            usd_to_cad
        ]
        mxn_history = [
            round(usd_to_mxn - random.uniform(0, 0.1), 4),
            round(usd_to_mxn - random.uniform(0, 0.05), 4),
            usd_to_mxn
        ]
        cny_history = [
            round(usd_to_cny - random.uniform(0, 0.05), 4),
            round(usd_to_cny - random.uniform(0, 0.03), 4),
            usd_to_cny
        ]
        jpy_history = [
            round(usd_to_jpy - random.uniform(0, 0.5), 2),
            round(usd_to_jpy - random.uniform(0, 0.3), 2),
            usd_to_jpy
        ]

        # Determine trends (using the simulated sample)
        cad_trend = "strengthening" if cad_history[2] > cad_history[1] else "weakening"
        mxn_trend = "strengthening" if mxn_history[2] > mxn_history[1] else "weakening"
        cny_trend = "strengthening" if cny_history[2] > cny_history[1] else "weakening"
        jpy_trend = "strengthening" if jpy_history[2] > jpy_history[1] else "weakening"

        cad_analysis = (
            "The USD is strengthening vs. CAD. This may benefit consumers but hurt exporters."
            if cad_trend == "strengthening" else
            "The USD is weakening vs. CAD. Exporters might benefit."
        )
        mxn_analysis = (
            "The USD is strengthening vs. MXN. This may benefit consumers but hurt exporters."
            if mxn_trend == "strengthening" else
            "The USD is weakening vs. MXN. Exporters might benefit."
        )
        cny_analysis = (
            "The USD is strengthening vs. CNY. This may benefit consumers but hurt exporters."
            if cny_trend == "strengthening" else
            "The USD is weakening vs. CNY. Exporters might benefit."
        )
        jpy_analysis = (
            "The USD is strengthening vs. JPY. This may benefit consumers but hurt exporters."
            if jpy_trend == "strengthening" else
            "The USD is weakening vs. JPY. Exporters might benefit."
        )

        return jsonify({
            "CAD": {
                "current": usd_to_cad,
                "history": cad_history,
                "trend": cad_trend,
                "analysis": cad_analysis
            },
            "MXN": {
                "current": usd_to_mxn,
                "history": mxn_history,
                "trend": mxn_trend,
                "analysis": mxn_analysis
            },
            "CNY": {
                "current": usd_to_cny,
                "history": cny_history,
                "trend": cny_trend,
                "analysis": cny_analysis
            },
            "JPY": {
                "current": usd_to_jpy,
                "history": jpy_history,
                "trend": jpy_trend,
                "analysis": jpy_analysis
            },
            "Bitcoin": {
                "current": bitcoin_price
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/historical-data/24h")
def historical_data_24h():
    """
    Retrieve historical currency data for the past 24 hours.
    """
    try:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        logs = LogEntry.query.filter(LogEntry.timestamp >= time_limit).order_by(LogEntry.timestamp).all()
        if not logs:
            return jsonify({"error": "No historical data available for 24 hours"}), 404
        dates = [log.timestamp.strftime("%Y-%m-%d %H:%M") for log in logs]
        cad = [log.usd_to_cad for log in logs]
        mxn = [log.usd_to_mxn for log in logs]
        cny = [log.usd_to_cny for log in logs]
        jpy = [log.usd_to_jpy for log in logs]
        btc = [log.bitcoin_price for log in logs]
        return jsonify({
            "dates": dates,
            "cad": cad,
            "mxn": mxn,
            "cny": cny,
            "jpy": jpy,
            "bitcoin": btc
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/historical-data/7d")
def historical_data_7d():
    """
    Retrieve historical currency data for the past 7 days.
    """
    try:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        logs = LogEntry.query.filter(LogEntry.timestamp >= time_limit).order_by(LogEntry.timestamp).all()
        if not logs:
            return jsonify({"error": "No historical data available for 7 days"}), 404
        dates = [log.timestamp.strftime("%Y-%m-%d %H:%M") for log in logs]
        cad = [log.usd_to_cad for log in logs]
        mxn = [log.usd_to_mxn for log in logs]
        cny = [log.usd_to_cny for log in logs]
        jpy = [log.usd_to_jpy for log in logs]
        btc = [log.bitcoin_price for log in logs]
        return jsonify({
            "dates": dates,
            "cad": cad,
            "mxn": mxn,
            "cny": cny,
            "jpy": jpy,
            "bitcoin": btc
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Default historical data endpoint returns 30 days of data.
@app.route("/historical-data")
def historical_data_30d():
    """
    Retrieve historical currency data for the past 30 days.
    """
    try:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        logs = LogEntry.query.filter(LogEntry.timestamp >= time_limit).order_by(LogEntry.timestamp).all()
        if not logs:
            return jsonify({"error": "No historical data available for 30 days"}), 404
        dates = [log.timestamp.strftime("%Y-%m-%d") for log in logs]
        cad = [log.usd_to_cad for log in logs]
        mxn = [log.usd_to_mxn for log in logs]
        cny = [log.usd_to_cny for log in logs]
        jpy = [log.usd_to_jpy for log in logs]
        btc = [log.bitcoin_price for log in logs]
        return jsonify({
            "dates": dates,
            "cad": cad,
            "mxn": mxn,
            "cny": cny,
            "jpy": jpy,
            "bitcoin": btc
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analysis")
def analysis():
    """
    Compute historical trends from the past month's logs for each metric:
      - First value, Latest value, Highest, Lowest, Percent Change, and Trend.
    """
    try:
        one_month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        logs = LogEntry.query.filter(LogEntry.timestamp >= one_month_ago).order_by(LogEntry.timestamp).all()
        if not logs:
            return jsonify({"error": "Not enough data for analysis"}), 404

        def compute_stats(values):
            first = values[0]
            last = values[-1]
            highest = max(values)
            lowest = min(values)
            percent_change = ((last - first) / first * 100) if first != 0 else 0
            trend = "strengthening" if last > first else "weakening"
            return {
                "first": first,
                "latest": last,
                "highest": highest,
                "lowest": lowest,
                "percent_change": round(percent_change, 2),
                "trend": trend
            }

        cad_stats = compute_stats([log.usd_to_cad for log in logs])
        mxn_stats = compute_stats([log.usd_to_mxn for log in logs])
        cny_stats = compute_stats([log.usd_to_cny for log in logs])
        jpy_stats = compute_stats([log.usd_to_jpy for log in logs])
        btc_stats = compute_stats([log.bitcoin_price for log in logs])

        return jsonify({
            "USD_vs_CAD": cad_stats,
            "USD_vs_MXN": mxn_stats,
            "USD_vs_CNY": cny_stats,
            "USD_vs_JPY": jpy_stats,
            "Bitcoin": btc_stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/news")
@limiter.limit("10 per minute")
def news():
    """
    Fetch the latest forex/currency exchange news articles.
    """
    query = "forex currency exchange"
    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 5
    }
    try:
        news_response = requests.get(NEWS_API_URL, params=params)
        if news_response.status_code == 429:
            return jsonify({"error": "External News API rate limit reached. Please try again later."}), 429
        articles = news_response.json().get("articles", [])
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------
# Shutdown Scheduler on Exit
# -----------------------
import atexit
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    # In production, run this app using a production-ready WSGI server (e.g., Gunicorn)
    app.run(host="0.0.0.0", debug=False, use_reloader=False)
