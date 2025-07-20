from flask import Flask, render_template, send_from_directory, jsonify, request
import yfinance as yf
from datetime import datetime, timedelta
import requests
import json
import os

app = Flask(__name__)

# ✅ 설정
PRICE_THRESHOLD = 3.0
VOLUME_MULTIPLIER = 3.0
NEWS_API_KEY = "pub_af7cbc0a338a4f64aeba8b044a544dca"

TICKERS = ["IXHL", "STEM", "TELL", "CRSP", "APLD", "INPX", "CYCC", "BLAZ", "LMFA", "CW", "SAIC", "EXPO"]

FILTER_KEYWORDS = [
    "fda", "clinical", "임상", "phase 1", "phase 2", "phase 3", "clinical trial", "study results",
    "bio", "therapeutics", "oncology", "drug", "healthcare",
    "rebound", "strong recovery", "bounce back",
    "breakout", "explosive", "jumps", "spikes"
]

# ✅ 뉴스 수집
def fetch_news(ticker):
    url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q={ticker}&country=us&language=en&category=business"
    try:
        res = requests.get(url)
        articles = res.json().get("results", [])
        seen = set()
        filtered = []
        for a in articles:
            title = a.get("title", "").strip()
            link = a.get("link", "").strip()
            lowered = title.lower()
            if not title or not link:
                continue
            if not any(kw in lowered for kw in FILTER_KEYWORDS):
                continue
            key = title + link
            if key in seen:
                continue
            seen.add(key)
            filtered.append({
                "title": title,
                "link": link,
                "keyword": ticker
            })
            if len(filtered) >= 3:
                break
        return filtered
    except:
        return []

# ✅ 번역
def translate(text):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "ko",
            "dt": "t",
            "q": text
        }
        res = requests.get(url, params=params)
        return res.json()[0][0][0]
    except:
        return text

# ✅ 급등 + 조짐 종목 분석
def analyze_stocks():
    rising = []
    warning = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 10:
                continue

            recent_prices = df["Close"][-3:]
            price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            volume_now = df["Volume"][-1]
            volume_prev = df["Volume"][-10:-1].mean()
            volume_ratio = volume_now / volume_prev if volume_prev > 0 else 0

            news = fetch_news(ticker)
            has_news = bool(news)

            data = {
                "ticker": ticker,
                "open": round(df["Open"][0], 2),
                "latest": round(recent_prices[-1], 2),
                "percent": round(price_change, 2),
                "volume_now": int(volume_now),
                "volume_prev": int(volume_prev),
                "volume_ratio": round(volume_ratio, 2),
                "news": news,
                "has_news": has_news
            }

            if price_change >= PRICE_THRESHOLD and volume_ratio >= VOLUME_MULTIPLIER:
                rising.append(data)
            elif volume_ratio >= VOLUME_MULTIPLIER:
                warning.append(data)

        except Exception as e:
            print(f"{ticker} 분석 오류: {e}")
            continue

    return rising, warning

# ✅ 호재 뉴스 수집
def fetch_positive_news():
    url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&country=us&language=en&category=business"
    try:
        res = requests.get(url)
        articles = res.json().get("results", [])[:20]
        news = []
        seen_keys = set()

        for a in articles:
            title = a.get("title", "").strip()
            link = a.get("link", "").strip()
            lowered = title.lower()

            if not title or not link:
                continue
            if "nasdaq" not in lowered:
                continue
            key = title + link
            if key in seen_keys:
                continue
            seen_keys.add(key)
            translated = translate(title)
            news.append({
                "title": translated,
                "link": link,
                "keyword": a.get("creator", [""])[0] if a.get("creator") else ""
            })

        today = datetime.now().strftime("%Y-%m-%d")
        filepath = "positive_news.json"
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = {}

        if today not in existing:
            existing[today] = []

        existing_keys = set(n["title"] + n["link"] for n in existing[today])
        for item in news:
            key = item["title"] + item["link"]
            if key not in existing_keys:
                existing[today].append(item)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        return news
    except Exception as e:
        print("호재 뉴스 오류:", e)
        return []

# ✅ 뉴스 수동 삭제
@app.route("/delete_news", methods=["POST"])
def delete_news():
    data = request.get_json()
    date = data.get("date")
    link = data.get("link")
    try:
        filepath = "positive_news.json"
        with open(filepath, "r", encoding="utf-8") as f:
            news_data = json.load(f)
        if date in news_data:
            news_data[date] = [n for n in news_data[date] if n["link"] != link]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(news_data, f, ensure_ascii=False, indent=2)
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ✅ 라우팅
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/data.json")
def merged_data():
    rising, warning = analyze_stocks()
    fetch_positive_news()

    try:
        with open("positive_news.json", "r", encoding="utf-8") as f:
            positive = json.load(f)
    except:
        positive = {}

    return jsonify({
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "spikes": rising,
        "watchlist": warning,
        "positive_news": positive
    })

@app.route("/run")
def manual_run():
    analyze_stocks()
    fetch_positive_news()
    return jsonify({"status": "done"})

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
