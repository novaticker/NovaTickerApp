from flask import Flask, render_template_string
import yfinance as yf
from datetime import datetime, timedelta
import requests
import json
import os

app = Flask(__name__)

# ✅ 감시 기준 설정
PRICE_THRESHOLD = 2.0  # 상승률 %
VOLUME_MULTIPLIER = 5.0  # 거래량 증가 배수
NEWS_API_KEY = "pub_af7cbc0a338a4f64aeba8b044a544dca"

# ✅ 감시할 티커 리스트
TICKERS = ["IXHL", "STEM", "TELL", "MINK", "INNX", "BNRG", "ABVE", "ZAPP", "BNL", "ADTX"]

# ✅ 필터링 키워드 (단타 가능한 강한 뉴스만, 필터 완화)
FILTER_KEYWORDS = [
    "fda", "approval", "phase 1", "phase 2", "phase 3", "clinical trial", "study results",
    "breakthrough", "merger", "acquisition", "surge", "spike", "explode", "skyrock", "positive results",
    "strategic partnership", "expand", "collaboration", "contract award", "granted", "received funding"
]

NEWS_FILE = "positive_news.json"

def load_news():
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_news(news_data):
    with open(NEWS_FILE, "w") as f:
        json.dump(news_data, f, indent=2)

def clean_old_news(news_data):
    today = datetime.utcnow().date()
    return {date: items for date, items in news_data.items()
            if (today - datetime.strptime(date, "%Y-%m-%d").date()).days <= 2}

def get_filtered_news(ticker):
    url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q={ticker}&language=en&country=us"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("results", [])
        filtered = []
        for article in articles:
            title = article.get("title", "").lower()
            link = article.get("link", "")
            if any(keyword in title for keyword in FILTER_KEYWORDS):
                filtered.append({"title": article.get("title"), "link": link})
        return filtered
    return []

@app.route("/")
def index():
    now = datetime.utcnow()
    matched_stocks = []
    for ticker in TICKERS:
        data = yf.Ticker(ticker)
        hist = data.history(period="2d", interval="1m")
        if len(hist) < 10:
            continue
        latest = hist.iloc[-1]
        earlier = hist.iloc[0]
        price_change = ((latest["Close"] - earlier["Close"]) / earlier["Close"]) * 100
        volume_change = latest["Volume"] / (hist["Volume"].mean() + 1)

        if price_change >= PRICE_THRESHOLD and volume_change >= VOLUME_MULTIPLIER:
            matched_stocks.append({
                "ticker": ticker,
                "price_change": round(price_change, 2),
                "volume_change": round(volume_change, 2),
                "news": get_filtered_news(ticker)
            })

    news_data = load_news()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    if today not in news_data:
        news_data[today] = []

    for stock in matched_stocks:
        for news in stock["news"]:
            if news not in news_data[today]:
                news_data[today].append(news)

    news_data = clean_old_news(news_data)
    save_news(news_data)

    return render_template_string(TEMPLATE,
                                  matched_stocks=matched_stocks,
                                  news_data=news_data,
                                  last_updated=now.strftime("%Y-%m-%d"))

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NovaTicker 리치</title>
    <style>
        body { font-family: sans-serif; background: #111; color: white; text-align: center; }
        .tab { padding: 10px 20px; margin: 5px; border-radius: 10px; display: inline-block; cursor: pointer; }
        .active { background: #00c896; color: white; }
        .inactive { background: #444; color: white; }
        .card { background: #222; margin: 10px auto; padding: 15px; width: 90%; border-radius: 10px; text-align: left; }
        a { color: #00c896; text-decoration: none; }
    </style>
</head>
<body>
    <h2>📊 NovaTicker 리치</h2>
    <div>
        <span class="tab inactive" onclick="showTab('spikes')">📈 급등 종목</span>
        <span class="tab active" onclick="showTab('news')">📰 호재 뉴스</span>
    </div>
    <div id="spikes" style="display:none;">
        {% if matched_stocks %}
            {% for stock in matched_stocks %}
                <div class="card">
                    <b>{{ stock.ticker }}</b> 🚀 {{ stock.price_change }}% / 📊 {{ stock.volume_change }}배
                    {% for item in stock.news %}
                        <div>📰 <a href="{{ item.link }}" target="_blank">{{ item.title }}</a></div>
                    {% endfor %}
                </div>
            {% endfor %}
        {% else %}
            <p>⏰ 마지막 갱신: 정보 없음</p>
            <p>📉 종목 없음</p>
        {% endif %}
    </div>
    <div id="news">
        <p>⏰ 마지막 갱신: {{ last_updated }}</p>
        {% if news_data %}
            {% for date, items in news_data.items() %}
                <h4>📅 {{ date }}</h4>
                {% for item in items %}
                    <div class="card">
                        📰 <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                    </div>
                {% endfor %}
            {% endfor %}
        {% else %}
            <p>📭 뉴스 없음</p>
        {% endif %}
    </div>
    <script>
        function showTab(tab) {
            document.getElementById('spikes').style.display = tab === 'spikes' ? 'block' : 'none';
            document.getElementById('news').style.display = tab === 'news' ? 'block' : 'none';
            let tabs = document.getElementsByClassName('tab');
            for (let t of tabs) {
                t.classList.remove('active');
                t.classList.add('inactive');
            }
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
