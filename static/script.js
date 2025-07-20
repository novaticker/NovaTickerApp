function showTab(tabId) {
  document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.content').forEach(div => div.classList.remove('active'));
  document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

function filterNews(keyword) {
  document.querySelectorAll('.filter-button').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.news-item').forEach(item => {
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

    // ✅ 호재 뉴스 (모든 날짜 순회)
    const newsData = data.positive_news || {};
    const newsListDiv = document.getElementById('news-list');
    newsListDiv.innerHTML = '';

    const dates = Object.keys(newsData).sort().reverse();
    if (dates.length === 0) {
      newsListDiv.innerHTML = '<p>📭 등록된 호재 뉴스가 없습니다</p>';
    } else {
      dates.forEach(date => {
        const section = document.createElement('div');
        section.innerHTML = `<h3>🗓️ ${date}</h3>`;
        newsData[date].forEach(n => {
          const item = document.createElement('div');
          item.className = 'news-item';
          item.innerHTML = `
            <button class="delete-btn" onclick="deleteNews('${date}', '${n.title.replace(/'/g, "\\'")}')">🗑️</button>
            <div class="news-title"><a href="${n.link}" target="_blank">${n.title}</a></div>
          `;
          section.appendChild(item);
        });
        newsListDiv.appendChild(section);
      });
    }
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
