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
    const res = await fetch('/data.json');
    const data = await res.json();
    const now = new Date().toISOString().split('T')[0];

    // ✅ 급등 종목
    const rising = data.rising || [];
    document.getElementById('rising-list').innerHTML = `<p>📅 ${now}</p>` + (
      rising.length
        ? rising.map(i => {
            const mark = i.news ? '⭐' : '';
            return `<div>${i.symbol} ${mark}
              ${i.news ? `<div class="news-title"><a href="${i.news.link}" target="_blank">${i.news.title}</a></div>` : ''}
            </div>`;
          }).join('<hr>')
        : '<p>📭 급등 종목 없음</p>'
    );

    // ✅ 급등 조짐
    const signal = data.signal || [];
    document.getElementById('signal-list').innerHTML = `<p>📅 ${now}</p>` + (
      signal.length
        ? signal.map(i => {
            const mark = i.news ? '⭐' : '';
            return `<div>${i.symbol} ${mark}
              ${i.news ? `<div class="news-title"><a href="${i.news.link}" target="_blank">${i.news.title}</a></div>` : ''}
            </div>`;
          }).join('<hr>')
        : '<p>📭 조짐 종목 없음</p>'
    );

    // ✅ 호재 뉴스
    const newsList = data.positive_news?.[now] || [];
    document.getElementById('news-list').innerHTML = newsList.length
      ? newsList.map(n => `
        <div class="news-item">
          <button class="delete-btn" onclick="deleteNews('${now}', '${n.title.replace(/'/g, "\\'")}')">🗑️</button>
          <div class="news-title"><a href="${n.link}" target="_blank">${n.title}</a></div>
        </div>
      `).join('')
      : '<p>📭 오늘의 호재 뉴스가 없습니다</p>';
  } catch (e) {
    console.error('❌ 데이터 로드 실패:', e);
    document.getElementById('rising-list').innerText = '⚠️ 급등 종목 로딩 실패';
    document.getElementById('signal-list').innerText = '⚠️ 조짐 종목 로딩 실패';
    document.getElementById('news-list').innerText = '⚠️ 뉴스 로딩 실패';
  }
}

async function deleteNews(date, title) {
  const res = await fetch('/delete_news', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date, title })
  });
  if (res.ok) loadData();
}

loadData();
