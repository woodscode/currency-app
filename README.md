# Currency Tracker Application

The Currency Tracker Application is a Flask-based web app that displays real-time currency exchange rates (USD vs. CAD, MXN, CNY, JPY) and Bitcoin prices. It also fetches relevant news articles using the [News API](https://newsapi.org/). The app periodically logs data into a SQLite database using APScheduler and uses Redis for persistent rate limiting via Flask-Limiter. The entire project is containerized using Docker Compose for a simple "docker up and go" deployment.

> **Note:** The only required configuration is to provide your News API key via a `.env` file.

## Features

- **Real-Time Data:**  
  Fetches current exchange rates and Bitcoin prices.
- **Historical Data Logging:**  
  Logs currency data periodically into a SQLite database using APScheduler.
- **News Integration:**  
  Retrieves the latest news articles related to currency exchange.
- **Persistent Rate Limiting:**  
  Uses Redis (via Flask-Limiter) to enforce API rate limits across container restarts.
- **Dockerized Deployment:**  
  Run the entire application stack using Docker Compose.
- **Minimal Setup:**  
  The only required configuration is setting your News API key via a `.env` file.
Application Endpoints
/
Renders the main index page.

/currency-data
Returns current exchange rates and a simulated 3-day historical dataset for demonstration purposes.

/historical-data/24h
Returns logged currency data for the past 24 hours.

/historical-data/7d
Returns logged currency data for the past 7 days.

/historical-data
Returns logged currency data for the past 30 days.

/analysis
Provides computed statistics (such as trends and percentage changes) based on logged data.

/news
Retrieves recent news articles related to currency exchange (rate limited to 10 requests per minute).

/debug
Displays a debug page with information on database log entries and the scheduler status.

## Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Getting Started

### 1. Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/your-username/currency-app.git
cd currency-app

