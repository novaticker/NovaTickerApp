from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
import requests
from googletrans import Translator
import pytz

app = Flask(__name__, template_folder='templates')
CORS(app)

NEWS_API_KEY = 'pub_af7cbc0a338a4f64aeba8b044a544dca'
NEWS_FILE = 'positive_news.json'

SYMBOLS = [
    'nasdaq', 'fda', 'clinical trial', 'phase 1', 'phase 2', 'phase 3',
    'merger', 'approval', 'biotech', 'pharma', 'listing',
    'acquisition', 'positive result', 'breakthrough',
    '암치료', '신약 승인', '신약 성공', '상장 승인', '임상 성공'
]

translator = Translator()
KST = pytz.timezone('Asia/Seoul')

@app.route('/')
def index():
    return render_template('index.html')

def fetch_news(query):
    url = f'https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q={query}&country=us&language=en&category=business'
    try:
        res = requests.get(url).json()
    except:
        return []

    articles = res.get('results', [])
    filtered = []

    for a in articles:
        if not isinstance(a, dict):
            continue

        title = a.get('title', '')
        link = a.get('link', '')

        if not link or 'example.com' in link:
            continue

        pub_utc = a.get('pubDate')
        if pub_utc:
            try:
                utc_dt = datetime.strptime(pub_utc, "%Y-%m-%d %H:%M:%S")
                kst_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(KST)
            except:
                kst_dt = datetime.now(KST)
        else:
            kst_dt = datetime.now(KST)

        try:
            translated = translator.translate(title, dest='ko').text
        except:
            translated = title

        filtered.append({
            'title': translated,
            'link': link,
            'symbol': query,
            'time': kst_dt.strftime("%H:%M"),
            'date': kst_dt.strftime("%Y-%m-%d"),
            'timestamp': kst_dt.strftime("%Y-%m-%d %H:%M:%S")
        })

    print(f"[{query}] 수집된 뉴스 개수: {len(filtered)}")  # 로그 출력
    return filtered

def update_news():
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    all_keys = set()
    for sym in SYMBOLS:
        news_items = fetch_news(sym)
        for item in news_items:
            date = item.get("date")
            if not date:
                continue
            if date not in data:
                data[date] = []
            uniq_key = item['title'] + item['link']
            if uniq_key not in all_keys:
                data[date].append(item)
                all_keys.add(uniq_key)

    for date in data:
        data[date].sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    cutoff = datetime.now(KST).replace(tzinfo=None) - timedelta(days=3)
    data = {
        date: items for date, items in data.items()
        if datetime.strptime(date, '%Y-%m-%d') >= cutoff
    }

    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def analyze_stocks():
    rising = []
    signal = []
    for sym in SYMBOLS[:5]:
        try:
            df = yf.download(sym, period="5d", interval="1m")
            if len(df) < 4:
                continue

            vol_now = df['Volume'].iloc[-1]
            vol_prev = df['Volume'].iloc[-4:-1].mean()
            price_now = df['Close'].iloc[-1]
            price_prev = df['Close'].iloc[-4]
            change = (price_now - price_prev) / price_prev * 100

            item = {'symbol': sym, 'volume': int(vol_now), 'change': round(change, 2)}

            news = get_related_news(sym)
            if news:
                item['news'] = news

            if vol_now > vol_prev * 2:
                if change >= 3:
                    rising.append(item)
                elif change >= 1:
                    signal.append(item)
        except Exception as e:
            print(f"{sym} 분석 오류:", e)
    return rising, signal

def get_related_news(symbol):
    today = datetime.now(KST).strftime('%Y-%m-%d')
    if not os.path.exists(NEWS_FILE):
        return None
    with open(NEWS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    today_news = data.get(today, [])
    for item in today_news:
        if symbol.lower() in item.get('title', '').lower():
            return item
    return None

@app.route('/data.json')
def get_data():
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            news = json.load(f)
    except:
        news = {}

    try:
        rising, signal = analyze_stocks()
    except:
        rising, signal = [], []

    updated_time = datetime.utcnow().isoformat()

    return jsonify({
        'rising': rising,
        'signal': signal,
        'positive_news': news,
        'updated': updated_time
    })

@app.route('/delete_news', methods=['POST'])
def delete_news():
    req = request.get_json()
    date = req.get('date')
    title = req.get('title')
    if not os.path.exists(NEWS_FILE):
        return jsonify({'error': 'no file'}), 404
    with open(NEWS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if date in data:
        data[date] = [n for n in data[date] if n['title'] != title]
        with open(NEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
