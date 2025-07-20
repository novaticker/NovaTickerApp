from flask import Flask, render_template, jsonify, request
import yfinance as yf
from datetime import datetime
import requests
import json
import os

app = Flask(__name__)

PRICE_THRESHOLD = 3.0
VOLUME_MULTIPLIER = 3.0
NEWS_API_KEY = "pub_af7cbc0a338a4f64aeba8b044a544dca"

TICKERS = ["IXHL", "STEM", "TELL", "CRSP", "APLD", "INPX", "CYCC", "BLAZ", "LMFA", "CW", "SAIC", "EXPO"]

FILTER_KEYWORDS = [
    "fda", "clinical trial", "임상", "phase 1", "phase 2", "phase 3", "clinical", "study results",
    "바이오", "biotech", "급등", "폭등", "approval", "coin", "crypto"
]

THEME_CATEGORIES = {
    "fda": ["fda", "임상", "clinical", "phase"],
    "bio": ["bio", "biotech", "바이오"],
    "rebound": ["급락", "반등"],
    "soaring": ["급등", "폭등"]
}

NEWS_PATH = "positive_news.json"

# 뉴스 번역
def translate(text):
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ko&dt=t&q=" + text
        res = requests.get(url)
        return res.json()[0][0][0]
    except:
        return text

# 뉴스 수집 및 저장
def fetch_and_store_news():
    today = datetime.utcnow().strftime('%Y-%m-%d')
    url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&country=us&language=en&category=business"
    res = requests.get(url)
    data = res.json()

    if not os.path.exists(NEWS_PATH):
        with open(NEWS_PATH, "w") as f:
            json.dump({}, f)

    with open(NEWS_PATH, "r") as f:
        news_data = json.load(f)

    news_data.setdefault(today, [])
    added_titles = {n['title'] for n in news_data[today]}

    for article in data.get("results", []):
        title = article.get("title", "")
        link = article.get("link", "")
        if "nasdaq" in title.lower() and not any(t in title for t in added_titles):
            if any(keyword.lower() in title.lower() for keyword in FILTER_KEYWORDS):
                translated = translate(title)
                news_data[today].append({
                    "title": translated,
                    "link": link
                })

    with open(NEWS_PATH, "w") as f:
        json.dump(news_data, f, indent=2, ensure_ascii=False)

# 급등 감지
def detect_rising_stocks():
    rising = []
    preparing = []
    news_map = load_news_map()

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if len(df) < 2: continue
            open_price = df["Open"].iloc[0]
            close_price = df["Close"].iloc[-1]
            volume_now = df["Volume"].iloc[-1]
            avg_volume = df["Volume"].mean()

            change = ((close_price - open_price) / open_price) * 100
            volume_ratio = volume_now / avg_volume if avg_volume > 0 else 0

            label = f"{ticker} ⭐" if ticker in news_map else ticker

            if change >= PRICE_THRESHOLD and volume_ratio >= VOLUME_MULTIPLIER:
                rising.append(label)
            elif volume_ratio >= VOLUME_MULTIPLIER and change >= 1.0:
                preparing.append(label)
        except Exception as e:
            print("분석 오류:", ticker, e)
    return rising, preparing

# 뉴스 매핑
def load_news_map():
    news_map = {}
    if not os.path.exists(NEWS_PATH): return news_map
    with open(NEWS_PATH, "r") as f:
        data = json.load(f)
    for date in data:
        for item in data[date]:
            for ticker in TICKERS:
                if ticker in item["title"].upper():
                    news_map.setdefault(ticker, []).append(item["title"])
    return news_map

@app.route("/")
def index():
    fetch_and_store_news()
    return render_template("index.html")

@app.route("/rising_stocks.json")
def rising_data():
    rising, preparing = detect_rising_stocks()
    return jsonify({"rising": rising, "preparing": preparing})

@app.route("/positive_news.json")
def get_news():
    if not os.path.exists(NEWS_PATH):
        return jsonify({})
    with open(NEWS_PATH, "r") as f:
        return jsonify(json.load(f))

@app.route("/delete_news", methods=["POST"])
def delete_news():
    data = request.get_json()
    date, title = data["date"], data["title"]
    with open(NEWS_PATH, "r") as f:
        all_news = json.load(f)
    if date in all_news:
        all_news[date] = [n for n in all_news[date] if n["title"] != title]
    with open(NEWS_PATH, "w") as f:
        json.dump(all_news, f, indent=2, ensure_ascii=False)
    return jsonify({"status": "ok"})

@app.route("/filter_keywords.json")
def filter_keywords():
    return jsonify(THEME_CATEGORIES)

if __name__ == "__main__":
    app.run(debug=True)
