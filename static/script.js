let currentTab = 'rising';
let rawData = null;

document.addEventListener('DOMContentLoaded', async () => {
  const res = await fetch('/data.json');
  const data = await res.json();
  rawData = data;
  document.getElementById('date').textContent = '📅 ' + new Date().toISOString().slice(0, 10);
  updateTab('rising');

  document.getElementById('tab-rising').addEventListener('click', () => updateTab('rising'));
  document.getElementById('tab-signal').addEventListener('click', () => updateTab('signal'));
  document.getElementById('tab-news').addEventListener('click', () => updateTab('news'));

  // 뉴스 필터 버튼 이벤트 등록
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const keyword = btn.dataset.keyword;
      if (keyword === 'reset') {
        renderNews(rawData.positive_news);
      } else {
        const filtered = {};
        for (const date in rawData.positive_news) {
          filtered[date] = rawData.positive_news[date].filter(n =>
            n.title.includes(keyword)
          );
        }
        renderNews(filtered);
      }
    });
  });
});

function updateTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  document.getElementById(`tab-${tab}`).classList.add('active');

  document.getElementById('rising-section').style.display = tab === 'rising' ? 'block' : 'none';
  document.getElementById('signal-section').style.display = tab === 'signal' ? 'block' : 'none';
  document.getElementById('news-section').style.display = tab === 'news' ? 'block' : 'none';

  if (tab === 'rising') renderStockList('rising');
  if (tab === 'signal') renderStockList('signal');
  if (tab === 'news') renderNews(rawData.positive_news);
}

function renderStockList(type) {
  const list = rawData[type];
  const container = document.getElementById(`${type}-list`);
  container.innerHTML = '';

  if (list.length === 0) {
    container.innerHTML = '<p>📛 종목 없음</p>';
    return;
  }

  list.forEach(item => {
    const div = document.createElement('div');
    div.className = 'stock-item';
    let content = `📈 <b>${item.symbol}</b> (${item.change}%) 거래량: ${item.volume.toLocaleString()}`;
    if (item.news) {
      content += ` <a href="${item.news.link}" target="_blank">⭐ ${item.news.title}</a>`;
    }
    div.innerHTML = content;
    container.appendChild(div);
  });
}

function renderNews(newsData) {
  const container = document.getElementById('news-list');
  container.innerHTML = '';
  let hasNews = false;

  for (const date in newsData) {
    if (!newsData[date] || newsData[date].length === 0) continue;
    hasNews = true;

    const dateTitle = document.createElement('h4');
    dateTitle.textContent = `🗓 ${date}`;
    container.appendChild(dateTitle);

    newsData[date].forEach(item => {
      const div = document.createElement('div');
      div.className = 'news-item';
      div.innerHTML = `
        <a href="${item.link}" target="_blank">📰 ${item.title}</a>
        <button class="delete-btn" onclick="deleteNews('${date}', \`${item.title}\`)">🗑️</button>
      `;
      container.appendChild(div);
    });
  }

  if (!hasNews) {
    container.innerHTML = '<p>🔍 뉴스 없음</p>';
  }
}

async function deleteNews(date, title) {
  const res = await fetch('/delete_news', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date, title })
  });

  if (res.ok) {
    rawData.positive_news[date] = rawData.positive_news[date].filter(n => n.title !== title);
    renderNews(rawData.positive_news);
  }
}
