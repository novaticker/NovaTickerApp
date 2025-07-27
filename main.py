from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
from datetime import datetime
import os
import pytz

app = Flask(__name__, template_folder='templates')
CORS(app)

NEWS_FILE = 'positive_news.json'
KST = pytz.timezone('Asia/Seoul')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_news')
def trigger_update_news():
    from background_news_updater import update_news
    try:
        update_news()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/data.json')
def get_data():
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            raw_news = json.load(f)
    except:
        raw_news = {}

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
