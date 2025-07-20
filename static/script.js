document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.tab-button');
  const contents = document.querySelectorAll('.tab-content');
  const newsContainer = document.getElementById('news-container');
  const risingContainer = document.getElementById('rising-container');
  const signalContainer = document.getElementById('signal-container');
  const lastUpdated = document.getElementById('last-updated');
  const filterButtons = document.querySelectorAll('.filter-button');
  const resetButton = document.getElementById('reset-button');

  let allNews = [];

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const target = tab.getAttribute('data-tab');
      contents.forEach(c => {
        c.style.display = c.id === target ? 'block' : 'none';
      });
    });
  });

  function createDeleteButton(date, title) {
    const btn = document.createElement('span');
    btn.textContent = '🗑️';
    btn.style.cursor = 'pointer';
    btn.style.marginLeft = '10px';
    btn.onclick = () => {
      fetch('https://novatickerapp.onrender.com/delete_news', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, title })
      }).then(() => {
        loadData(); // 삭제 후 다시 로드
      });
    };
    return btn;
  }

  function createNewsItem(item, date) {
    const div = document.createElement('div');
    div.className = 'news-item';
    const link = document.createElement('a');
    link.href = item.link;
    link.target = '_blank';
    link.textContent = `📰 ${item.title}`;
    div.appendChild(link);
    div.appendChild(createDeleteButton(date, item.title));
    return div;
  }

  function createStockItem(stock) {
    const div = document.createElement('div');
    div.className = 'stock-item';
    div.innerHTML = `
      <strong>${stock.symbol}</strong> (${stock.change}%) 📊 거래량: ${stock.volume}
      ${stock.news ? `<br><a href="${stock.news.link}" target="_blank">📰 ${stock.news.title}</a>` : ''}
    `;
    if (stock.news) {
      div.innerHTML = `<strong>${stock.symbol} ⭐</strong> (${stock.change}%) 📊 거래량: ${stock.volume}<br><a href="${stock.news.link}" target="_blank">📰 ${stock.news.title}</a>`;
    }
    return div;
  }

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const keyword = btn.getAttribute('data-filter');
      const filtered = allNews.filter(item => item.title.includes(keyword));
      renderNews(filtered);
    });
  });

  resetButton.addEventListener('click', () => {
    renderNews(allNews);
  });

  function renderNews(news) {
    newsContainer.innerHTML = '';
    news.forEach(item => {
      const newsItem = createNewsItem(item.item, item.date);
      newsContainer.appendChild(newsItem);
    });
  }

  function loadData() {
    lastUpdated.textContent = '⏰ 마지막 갱신: 불러오는 중...';
    fetch('https://novatickerapp.onrender.com/data.json')
      .then(res => res.json())
      .then(data => {
        newsContainer.innerHTML = '';
        allNews = [];
        for (const date in data.positive_news) {
          data.positive_news[date].forEach(item => {
            allNews.push({ date, item });
          });
        }
        renderNews(allNews);

        risingContainer.innerHTML = '';
        data.rising.forEach(stock => {
          risingContainer.appendChild(createStockItem(stock));
        });

        signalContainer.innerHTML = '';
        data.signal.forEach(stock => {
          signalContainer.appendChild(createStockItem(stock));
        });

        const now = new Date();
        const timeStr = now.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
        lastUpdated.textContent = `⏰ 마지막 갱신: ${timeStr}`;
      });
  }

  loadData();
  setInterval(loadData, 60000); // 1분마다 갱신
});
