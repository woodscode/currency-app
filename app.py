from flask import Flask, render_template, jsonify, request
import requests
import os
import datetime
import logging
import atexit

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

# -----------------------
# Logging Configuration
# -----------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------
# Flask Application Setup
# -----------------------
app = Flask(__name__)

# Rate Limiter: 100 requests per hour per IP
# For production, consider setting REDIS_URL in your environment to use persistent storage.
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100 per hour"],
        storage_uri=REDIS_URL
    )
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=["100 per hour"])
limiter.init_app(app)

# Caching configuration (in-memory cache with a 10-minute timeout)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# Database configuration (using SQLite)
# Using an absolute path so that the DB file is stored in /app/data inside the container.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/data/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -----------------------
# Database Model
# -----------------------
class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    usd_to_cad = db.Column(db.Float, nullable=False)
    usd_to_mxn = db.Column(db.Float, nullable=False)
    usd_to_cny = db.Column(db.Float, nullable=False)
    usd_to_jpy = db.Column(db.Float, nullable=False)
    bitcoin_price = db.Column(db.Float, nullable=False)

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
    except Exception as e:
        logger.error("Error fetching Bitcoin price: %s", e)
        return 0

def log_currency_data():
    """
    Fetch current exchange rates and Bitcoin price,
    then log these values to the database.
    This function is wrapped in an application context so it works correctly with APScheduler.
    """
    with app.app_context():
        try:
            response = requests.get(CURRENCY_API_URL)
            data = response.json()
            rates = data.get("rates", {})
            usd_to_cad = rates.get("CAD")
            usd_to_mxn = rates.get("MXN")
            usd_to_cny = rates.get("CNY")
            usd_to_jpy = rates.get("JPY")
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
            logger.info(
                "Logged data at %s: CAD=%s, MXN=%s, CNY=%s, JPY=%s, BTC=%s",
                datetime.datetime.utcnow(), usd_to_cad, usd_to_mxn, usd_to_cny, usd_to_jpy, bitcoin_price
            )
        except Exception as e:
            logger.error("Error logging currency data: %s", e)

def compute_stats(values):
    """Compute statistics (first, latest, highest, lowest, percent change, trend) from a list of values."""
    if not values:
        return {}
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

# -----------------------
# APScheduler: Periodic Data Logging
# -----------------------
scheduler = BackgroundScheduler()
scheduler.add_job(func=log_currency_data, trigger="interval", minutes=15)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# -----------------------
# Routes
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/currency-data")
@limiter.limit("50 per hour")
def currency_data():
    """
    Fetch current exchange rates and Bitcoin price,
    then generate a simulated 3-day history for demonstration.
    """
    try:
        response = requests.get(CURRENCY_API_URL)
        data = response.json()
        rates = data.get("rates", {})
        usd_to_cad = rates.get("CAD")
        usd_to_mxn = rates.get("MXN")
        usd_to_cny = rates.get("CNY")
        usd_to_jpy = rates.get("JPY")
        bitcoin_price = get_bitcoin_price()

        # Generate simulated 3-day history for demonstration
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

        cad_trend = "strengthening" if cad_history[2] > cad_history[1] else "weakening"
        mxn_trend = "strengthening" if mxn_history[2] > mxn_history[1] else "weakening"
        cny_trend = "strengthening" if cny_history[2] > cny_history[1] else "weakening"
        jpy_trend = "strengthening" if jpy_history[2] > jpy_history[1] else "weakening"

        analysis_text = lambda currency, trend: (
            f"The USD is strengthening vs. {currency}. This may benefit consumers but hurt exporters."
            if trend == "strengthening"
            else f"The USD is weakening vs. {currency}. Exporters might benefit."
        )

        return jsonify({
            "CAD": {
                "current": usd_to_cad,
                "history": cad_history,
                "trend": cad_trend,
                "analysis": analysis_text("CAD", cad_trend)
            },
            "MXN": {
                "current": usd_to_mxn,
                "history": mxn_history,
                "trend": mxn_trend,
                "analysis": analysis_text("MXN", mxn_trend)
            },
            "CNY": {
                "current": usd_to_cny,
                "history": cny_history,
                "trend": cny_trend,
                "analysis": analysis_text("CNY", cny_trend)
            },
            "JPY": {
                "current": usd_to_jpy,
                "history": jpy_history,
                "trend": jpy_trend,
                "analysis": analysis_text("JPY", jpy_trend)
            },
            "Bitcoin": {
                "current": bitcoin_price
            }
        })
    except Exception as e:
        logger.error("Error in /currency-data endpoint: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/historical-data/24h")
def historical_data_24h():
    try:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        logs = LogEntry.query.filter(LogEntry.timestamp >= time_limit).order_by(LogEntry.timestamp).all()
        if not logs:
            return jsonify({"error": "No historical data available for 24 hours"}), 404
        data = {
            "dates": [log.timestamp.strftime("%Y-%m-%d %H:%M") for log in logs],
            "cad": [log.usd_to_cad for log in logs],
            "mxn": [log.usd_to_mxn for log in logs],
            "cny": [log.usd_to_cny for log in logs],
            "jpy": [log.usd_to_jpy for log in logs],
            "bitcoin": [log.bitcoin_price for log in logs]
        }
        return jsonify(data)
    except Exception as e:
        logger.error("Error in /historical-data/24h endpoint: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/historical-data/7d")
def historical_data_7d():
    try:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        logs = LogEntry.query.filter(LogEntry.timestamp >= time_limit).order_by(LogEntry.timestamp).all()
        if not logs:
            return jsonify({"error": "No historical data available for 7 days"}), 404
        data = {
            "dates": [log.timestamp.strftime("%Y-%m-%d %H:%M") for log in logs],
            "cad": [log.usd_to_cad for log in logs],
            "mxn": [log.usd_to_mxn for log in logs],
            "cny": [log.usd_to_cny for log in logs],
            "jpy": [log.usd_to_jpy for log in logs],
            "bitcoin": [log.bitcoin_price for log in logs]
        }
        return jsonify(data)
    except Exception as e:
        logger.error("Error in /historical-data/7d endpoint: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/historical-data")
def historical_data_30d():
    try:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        logs = LogEntry.query.filter(LogEntry.timestamp >= time_limit).order_by(LogEntry.timestamp).all()
        if not logs:
            return jsonify({"error": "No historical data available for 30 days"}), 404
        data = {
            "dates": [log.timestamp.strftime("%Y-%m-%d") for log in logs],
            "cad": [log.usd_to_cad for log in logs],
            "mxn": [log.usd_to_mxn for log in logs],
            "cny": [log.usd_to_cny for log in logs],
            "jpy": [log.usd_to_jpy for log in logs],
            "bitcoin": [log.bitcoin_price for log in logs]
        }
        return jsonify(data)
    except Exception as e:
        logger.error("Error in /historical-data (30d) endpoint: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/analysis")
def analysis():
    try:
        one_month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        logs = LogEntry.query.filter(LogEntry.timestamp >= one_month_ago).order_by(LogEntry.timestamp).all()
        if not logs:
            return jsonify({"error": "Not enough data for analysis"}), 404

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
        logger.error("Error in /analysis endpoint: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/news")
@limiter.limit("10 per minute")
def news():
    params = {
        "q": "forex currency exchange",
        "apiKey": NEWS_API_KEY,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 5
    }
    try:
        news_response = requests.get(NEWS_API_URL, params=params)
        news_response.raise_for_status()
        try:
            data = news_response.json()
        except ValueError as json_err:
            logger.error("Error parsing JSON from news API. Response text: %s", news_response.text)
            return jsonify({"error": "Failed to parse JSON from news API"}), 500

        if news_response.status_code == 429:
            return jsonify({"error": "External News API rate limit reached. Please try again later."}), 429

        articles = data.get("articles", [])
        return jsonify(articles)
    except Exception as e:
        logger.error("Error fetching news: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/debug")
def debug():
    logs = LogEntry.query.order_by(LogEntry.timestamp.desc()).all()
    # Determine scheduler status
    from apscheduler.schedulers.base import STATE_RUNNING, STATE_PAUSED, STATE_STOPPED
    if scheduler.state == STATE_RUNNING:
        scheduler_status = "Running"
    elif scheduler.state == STATE_PAUSED:
        scheduler_status = "Paused"
    elif scheduler.state == STATE_STOPPED:
        scheduler_status = "Stopped"
    else:
        scheduler_status = "Unknown"

    html = "<h1>Debug Information</h1>"
    html += "<h2>Database Log Entries</h2>"
    if logs:
        html += """
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>USD to CAD</th>
                <th>USD to MXN</th>
                <th>USD to CNY</th>
                <th>USD to JPY</th>
                <th>Bitcoin Price</th>
            </tr>
        """
        for entry in logs:
            html += f"""
                <tr>
                    <td>{entry.id}</td>
                    <td>{entry.timestamp}</td>
                    <td>{entry.usd_to_cad}</td>
                    <td>{entry.usd_to_mxn}</td>
                    <td>{entry.usd_to_cny}</td>
                    <td>{entry.usd_to_jpy}</td>
                    <td>{entry.bitcoin_price}</td>
                </tr>
            """
        html += "</table>"
    else:
        html += "<p>No log entries found.</p>"
    html += f"<h2>Scheduler Status</h2><p>{scheduler_status}</p>"
    html += "<h2>Application Logs</h2><p>Check your server console or log file for application logs.</p>"
    return html

# -----------------------
# Application Entry Point
# -----------------------
if __name__ == "__main__":
    # Log currency data once on startup (wrapped in app context)
    with app.app_context():
        log_currency_data()
    app.run(host="0.0.0.0", debug=False, use_reloader=False)
