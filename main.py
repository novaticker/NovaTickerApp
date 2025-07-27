from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import os
from datetime import datetime
import pytz
from background_news_updater import update_news, get_today_top_gainers

app = Flask(__name__, template_folder='templates')
CORS(app)

NEWS_FILE = 'positive_news.json'
KST = pytz.timezone('Asia/Seoul')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_news')
def trigger_update_news():
    try:
        update_news()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/data.json')
def get_data():
    raw_news = {}
    try:
        if os.path.exists(NEWS_FILE):
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                raw_news = json.load(f)
    except:
        raw_news = {}

    try:
        rising, signal = get_today_top_gainers()
    except Exception as e:
        rising, signal = [], []

    def attach_news(slist):
        for item in slist:
            symbol = item.get('symbol')
            if not symbol:
                continue
            for date in raw_news:
                for n in raw_news[date]:
                    if n.get("symbol") == symbol:
                        item['news'] = {
                            "title": n.get('title', ''),
                            "summary": n.get('summary', ''),
                            "symbol": n.get('symbol', ''),
                            "time": n.get('time', ''),
                            "timestamp": n.get('timestamp', ''),
                            "source": n.get('source', '')
                        }
                        break
                if 'news' in item:
                    break
        return slist

    rising = attach_news(rising)
    signal = attach_news(signal)

    now_kst = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')

    return jsonify({
        'rising': rising,
        'signal': signal,
        'positive_news': raw_news,
        'updated': now_kst
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
