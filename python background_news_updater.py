import requests
import json
import os
import re
import pytz
from datetime import datetime
from bs4 import BeautifulSoup
from googletrans import Translator

NEWS_FILE = 'positive_news.json'
KST = pytz.timezone('Asia/Seoul')
translator = Translator()

NEWS_API_KEYS = [
    'pub_af7cbc0a338a4f64aeba8b044a544dca',
    'pub_dc30774b54994201bbe1e8ca725ba61f',
    'pub_cfed46877d8d41668ad220429f779cc3'
]

def extract_symbol(text):
    match = re.search(r'\b(NASDAQ|NYSE|AMEX)[:\s-]*([A-Z]{1,6})\b', text)
    if match:
        return match.group(2).upper()
    match2 = re.search(r'\b([A-Z]{2,5})[:：]', text)
    if match2:
        return match2.group(1).upper()
    return 'N/A'

def summarize(text):
    return text[:100] + "..." if len(text) > 100 else text

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
        content = a.get('content', '') or ''
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
            full_text = f"{title}. {content}"
            translated = translator.translate(full_text, dest='ko').text
        except:
            translated = title

        summary = summarize(translated.strip().replace('\n', ' '))
        matched_symbol = extract_symbol(title)

        results.append({
            'title': translated,
            'summary': summary,
            'link': link.strip(),
            'symbol': matched_symbol,
            'time': kst_dt.strftime('%H:%M'),
            'date': kst_dt.strftime('%Y-%m-%d'),
            'timestamp': kst_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'source': a.get('source_id', 'NewsData') or 'NewsData'
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
            summary = summarize(translated)
            symbol = extract_symbol(title)
            news_list.append({
                'title': translated,
                'summary': summary,
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
            summary = summarize(translated)
            symbol = extract_symbol(title)
            news_list.append({
                'title': translated,
                'summary': summary,
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

    api_index = 0
    for query in ['nasdaq', 'ipo', 'fda', 'merger', 'pharma']:
        news = fetch_news(query, NEWS_API_KEYS[api_index])
        for item in news:
            date = item['date']
            key = item['title'] + item['link']
            if key not in all_keys:
                data.setdefault(date, []).append(item)
                all_keys.add(key)
        api_index = (api_index + 1) % len(NEWS_API_KEYS)

    for fn in [crawl_yahoo, crawl_prnewswire]:
        for item in fn():
            date = item['date']
            key = item['title'] + item['link']
            if key not in all_keys:
                data.setdefault(date, []).append(item)
                all_keys.add(key)

    for date in data:
        data[date].sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
