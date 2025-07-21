from flask import Flask, jsonify, request, render_template  
from flask_cors import CORS  
import yfinance as yf  
from datetime import datetime  
import json  
import os  
import requests  
from googletrans import Translator  
import pytz  
import re  
from bs4 import BeautifulSoup  
  
app = Flask(__name__, template_folder='templates')  
CORS(app)  
  
NEWS_API_KEYS = [  
    'pub_af7cbc0a338a4f64aeba8b044a544dca',  
    'pub_dc30774b54994201bbe1e8ca725ba61f',  
    'pub_cfed46877d8d41668ad220429f779cc3'  
]  
  
NEWS_FILE = 'positive_news.json'  
KST = pytz.timezone('Asia/Seoul')  
translator = Translator()  
  
@app.route('/')  
def index():  
    return render_template('index.html')  
  
def extract_symbol(text):  
    match = re.search(r'(NASDAQ|NYSE|NYSEARCA|AMEX)[:：]?\s*([A-Z]+)', text, re.IGNORECASE)  
    if match:  
        return match.group(2).upper()  
    match2 = re.search(r'\b([A-Z]{2,5})[:：]', text)  
    if match2:  
        return match2.group(1).upper()  
    return 'N/A'  
  
def fetch_news(query, api_key):  
    url = f'https://newsdata.io/api/1/news?apikey={api_key}&q={query}&country=us&language=en&category=business'  
    try:  
        res = requests.get(url, timeout=10)  
        res.raise_for_status()  
        data = res.json()  
    except:  
        return []  
  
    articles = data.get('results', [])  
    results = []  
  
    for a in articles:  
        title = a.get('title', '')  
        link = a.get('link', '')  
        pub_utc = a.get('pubDate')  
        if not title or not link or not pub_utc:  
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
  
        matched_symbol = extract_symbol(title)  
  
        results.append({  
            'title': translated,  
            'link': link.strip(),  
            'symbol': matched_symbol,  
            'time': kst_dt.strftime('%H:%M'),  
            'date': kst_dt.strftime('%Y-%m-%d'),  
            'timestamp': kst_dt.strftime('%Y-%m-%d %H:%M:%S'),  
            'source': 'NewsData'  
        })  
  
    return results  
  
def crawl_yahoo():  
    try:  
        url = 'https://finance.yahoo.com/topic/stock-market-news'  
        headers = {'User-Agent': 'Mozilla/5.0'}  
        res = requests.get(url, headers=headers, timeout=10)  
        soup = BeautifulSoup(res.text, 'html.parser')  
        items = soup.select('li.js-stream-content')  
        news_list = []  
  
        for item in items:  
            a_tag = item.find('a')  
            if not a_tag or not a_tag.get('href'):  
                continue  
            title = a_tag.get_text(strip=True)  
            if len(title) < 6:  
                continue  
            link = a_tag['href']  
            if not link.startswith('http'):  
                link = 'https://finance.yahoo.com' + link  
            kst_dt = datetime.now(KST)  
            try:  
                translated = translator.translate(title, dest='ko').text  
            except:  
                translated = title  
            symbol = extract_symbol(title)  
            news_list.append({  
                'title': translated,  
                'link': link,  
                'symbol': symbol,  
                'time': kst_dt.strftime('%H:%M'),  
                'date': kst_dt.strftime('%Y-%m-%d'),  
                'timestamp': kst_dt.strftime('%Y-%m-%d %H:%M:%S'),  
                'source': 'Yahoo Finance'  
            })  
        return news_list  
    except:  
        return []  
  
def crawl_prnewswire():  
    try:  
        url = 'https://www.prnewswire.com/news-releases/news-releases-list/'  
        headers = {'User-Agent': 'Mozilla/5.0'}  
        res = requests.get(url, headers=headers, timeout=10)  
        soup = BeautifulSoup(res.text, 'html.parser')  
        items = soup.select('div.card')[:15]  
        news_list = []  
  
        for item in items:  
            a_tag = item.find('a')  
            if not a_tag:  
                continue  
            title = a_tag.get_text(strip=True)  
            link = 'https://www.prnewswire.com' + a_tag['href']  
            if len(title) < 6:  
                continue  
            kst_dt = datetime.now(KST)  
            try:  
                translated = translator.translate(title, dest='ko').text  
            except:  
                translated = title  
            symbol = extract_symbol(title)  
            news_list.append({  
                'title': translated,  
                'link': link,  
                'symbol': symbol,  
                'time': kst_dt.strftime('%H:%M'),  
                'date': kst_dt.strftime('%Y-%m-%d'),  
                'timestamp': kst_dt.strftime('%Y-%m-%d %H:%M:%S'),  
                'source': 'PRNewswire'  
            })  
        return news_list  
    except:  
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
  
    api_key_index = 0  
    for query in ['nasdaq', 'ipo', 'fda', 'merger', 'pharma']:  
        news_items = fetch_news(query, NEWS_API_KEYS[api_key_index])  
        for item in news_items:  
            date = item['date']  
            uniq = item['title'] + item['link']  
            if uniq not in all_keys:  
                data.setdefault(date, []).append(item)  
                all_keys.add(uniq)  
        api_key_index = (api_key_index + 1) % len(NEWS_API_KEYS)  
  
    for fetcher in [crawl_yahoo, crawl_prnewswire]:  
        for item in fetcher():  
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
    try:  
        update_news()  
        return jsonify({'status': 'ok'})  
    except Exception as e:  
        return jsonify({'status': 'error', 'message': str(e)}), 500  
  
def get_today_top_gainers():  
    try:  
        url = 'https://finance.yahoo.com/gainers'  
        headers = {'User-Agent': 'Mozilla/5.0'}  
        res = requests.get(url, headers=headers, timeout=10)  
        soup = BeautifulSoup(res.text, 'html.parser')  
        rows = soup.select('table tbody tr')  
        gainers, signals = [], []  
  
        for row in rows:  
            cols = row.find_all('td')  
            if len(cols) < 6:  
                continue  
            symbol = cols[0].text.strip()  
            change_percent = cols[4].text.strip().replace('%', '').replace('+', '')  
            try:  
                percent = float(change_percent)  
                label = f"{symbol} (+{percent:.1f}%)"  
                item = {  
                    'symbol': symbol,  
                    'change': percent,  
                    'label': label  
                }  
                if percent >= 5:  
                    gainers.append(item)  
                df = yf.download(symbol, period="5d", interval="1m")  
                if len(df) >= 4:  
                    vol_now = df['Volume'].iloc[-1]  
                    vol_prev = df['Volume'].iloc[-4:-1].mean()  
                    if vol_now > vol_prev * 2:  
                        signals.append(item)  
            except:  
                continue  
        return gainers, signals  
    except:  
        return [], []  
  
@app.route('/data.json')  
def get_data():  
    try:  
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:  
            raw_news = json.load(f)  
    except:  
        raw_news = {}  
    try:  
        rising, signal = get_today_top_gainers()  
    except:  
        rising, signal = [], []  
    updated_time = datetime.utcnow().isoformat()  
    return jsonify({  
        'rising': rising,  
        'signal': signal,  
        'positive_news': raw_news,  
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
