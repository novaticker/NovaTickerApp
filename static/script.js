<script>
  const BASE_URL = location.origin;

  function showTab(tabId) {
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.content').forEach(div => div.classList.remove('active'));
    document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
  }

  function filterNews(keyword) {
    document.querySelectorAll('.filter-button').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    const items = document.querySelectorAll('.news-item');
    items.forEach(item => {
      item.style.display = item.innerText.includes(keyword) ? 'block' : 'none';
    });
  }

  function resetFilter() {
    document.querySelectorAll('.filter-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.news-item').forEach(item => item.style.display = 'block');
  }

  async function loadData() {
    try {
      const res = await fetch(`${BASE_URL}/data.json`);
      const data = await res.json();
      const now = new Date().toISOString().split('T')[0];

      // 급등 종목
      const rising = data.rising || [];
      document.getElementById('rising-list').innerHTML = `<p>📅 ${now}</p>` + rising.map(i => {
        const mark = i.news ? '⭐' : '';
        return `<div>${i.symbol} ${mark} ${i.news ? `<div class="news-title"><a href="${i.news.link}" target="_blank">${i.news.title}</a></div>` : ''}</div>`;
      }).join('<hr>');

      // 급등 조짐
      const signal = data.signal || [];
      document.getElementById('signal-list').innerHTML = `<p>📅 ${now}</p>` + signal.map(i => {
        const mark = i.news ? '⭐' : '';
        return `<div>${i.symbol} ${mark} ${i.news ? `<div class="news-title"><a href="${i.news.link}" target="_blank">${i.news.title}</a></div>` : ''}</div>`;
      }).join('<hr>');

      // 호재 뉴스
      const newsList = data.positive_news[now] || [];
      document.getElementById('news-list').innerHTML = newsList.map(n => `
        <div class="news-item">
          <button class="delete-btn" onclick="deleteNews('${now}', '${n.title.replace(/'/g, "\\'")}')">🗑️</button>
          <div class="news-title"><a href="${n.link}" target="_blank">${n.title}</a></div>
        </div>
      `).join('');
    } catch (e) {
      console.error('데이터 불러오기 실패:', e);
    }
  }

  async function deleteNews(date, title) {
    const res = await fetch(`${BASE_URL}/delete_news`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, title })
    });
    if (res.ok) loadData();
  }

  loadData();
</script>
