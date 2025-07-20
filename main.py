from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
import pytz

app = Flask(__name__, template_folder='templates')
CORS(app)

NEWS_API_KEYS = [
    'pub_af7cbc0a338a4f64aeba8b044a544dca',
    'pub_dc30774b54994201bbe1e8ca725ba61f',
    'pub_cfed46877d8d41668ad220429f779cc3'
]

NEWS_FILE = 'positive_news.json'
STOCK_SYMBOLS = ['APLD', 'CYCC', 'LMFA', 'CW', 'SAIC']
ALLOWED_CHINA_SYMBOLS = ['nio', 'baba', 'bidu', 'jd']
KST = pytz.timezone('Asia/Seoul')
translator = Translator()

@app.route('/')
def index():
    return render_template('index.html')

def is_positive_news(news):
    title = news.get('title', '').lower()
    content = news.get('content', '').lower()

    positive_keywords = [
        'fda', 'approval', 'clinical', 'trial',
        'biotech', 'pharma', 'ipo', 'listing',
        'merger', 'acquisition', 'partnership', 'investment',
        'skyrocket', 'surge', 'breakout', 'jump',
        'launch', 'open', 'expand', 'expansion', 'event',
        'new technology', 'unveil', 'announce', 'release'
    ]

    exclude_keywords = [
        'crypto', 'bitcoin', 'ethereum',
        'lawsuit', 'china', 'hong kong', 'delisting', 'sec investigation'
    ]

    if not any(kw in title or kw in content for kw in positive_keywords):
        return False
    if any(kw in title or kw in content for kw in exclude_keywords):
        if not any(sym in title or sym in content for sym in ALLOWED_CHINA_SYMBOLS):
            return False
    return True

def fetch_news(query, api_key):
    url = f'https://newsdata.io/api/1/news?apikey={api_key}&q={query}&country=us&language=en&category=business'
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
    except:
        return []

    articles = data.get('results', [])
    filtered = []

    for a in articles:
        title = a.get('title', '')
        link = a.get('link', '')
        pub_utc = a.get('pubDate')
        if not title or not link or not pub_utc:
            continue
        if not is_positive_news(a):
            continue

        try:
            utc_dt = datetime.strptime(pub_utc, "%Y-%m-%d %H:%M:%S")
            kst_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(KST)
        except:
            kst_dt = datetime.now(KST)

        try:
            translated = translator.translate(title, dest='ko').text
        except:
            translated = title

        matched_symbol = ''
        for sym in STOCK_SYMBOLS:
            if sym.lower() in title.lower():
                matched_symbol = sym
                break

        filtered.append({
            'title': translated,
            'link': link,
            'symbol': matched_symbol,
            'time': kst_dt.strftime('%H:%M'),
            'date': kst_dt.strftime('%Y-%m-%d'),
            'timestamp': kst_dt.strftime('%Y-%m-%d %H:%M:%S')
        })

    return filtered

def crawl_stocktitan():
    url = 'https://www.stocktitan.net/news/'
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        news_blocks = soup.select('.news-row')
        news_list = []
        for block in news_blocks:
            title_tag = block.select_one('.news-row__title')
            meta_tag = block.select_one('.news-row__publisher')
            if not title_tag or not meta_tag:
                continue
            link = title_tag.get('href')
            title = title_tag.text.strip()
            symbol = meta_tag.text.strip().split()[0].replace(':', '')

            if not link.startswith('http'):
                link = 'https://www.stocktitan.net' + link

            kst_dt = datetime.now(KST)
            news_list.append({
                'title': title,
                'link': link,
                'symbol': symbol,
                'time': kst_dt.strftime('%H:%M'),
                'date': kst_dt.strftime('%Y-%m-%d'),
                'timestamp': kst_dt.strftime('%Y-%m-%d %H:%M:%S')
            })
        return news_list
    except Exception as e:
        print(f"[StockTitan] 크롤링 실패: {e}")
        return []

def update_news():
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    all_keys = set()
    for date_items in data.values():
        for item in date_items:
            all_keys.add(item['title'] + item['link'])

    # API 뉴스
    api_key_index = 0
    for query in ['nasdaq', 'fda', 'biotech', 'pharma', 'ipo', 'merger', 'investment']:
        news_items = fetch_news(query, NEWS_API_KEYS[api_key_index])
        for item in news_items:
            date = item['date']
            uniq = item['title'] + item['link']
            if uniq not in all_keys:
                data.setdefault(date, []).append(item)
                all_keys.add(uniq)
        api_key_index = (api_key_index + 1) % len(NEWS_API_KEYS)

    # StockTitan 뉴스
    titan_news = crawl_stocktitan()
    for item in titan_news:
        date = item['date']
        uniq = item['title'] + item['link']
        if uniq not in all_keys:
            data.setdefault(date, []).append(item)
            all_keys.add(uniq)

    for date in data:
        data[date].sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/update_news')
def trigger_update_news():
    update_news()
    return '✅ 뉴스 업데이트 완료'

def analyze_stocks():
    rising, signal = [], []
    for sym in STOCK_SYMBOLS:
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
            print(f"[분석 오류] {sym}: {e}")
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
    app.run(host='0.0.0.0', port=8080, debug=False)
