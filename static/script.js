const tabs = document.querySelectorAll('.tab-btn');
const contents = document.querySelectorAll('.content');
const newsContainer = document.getElementById('news');
const lastUpdated = document.getElementById('lastUpdated');
const filterButtons = document.querySelectorAll('.filter-btn');

let allNews = {};
let currentTab = 'rising';

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentTab = tab.dataset.tab;
    showContent();
  });
});

filterButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const filter = btn.dataset.filter;
    if (filter === 'reset') {
      showContent();
    } else {
      showFilteredNews(filter);
    }
  });
});

function showContent() {
  contents.forEach(c => c.style.display = 'none');
  if (currentTab === 'news') {
    document.getElementById('filter').style.display = 'block';
    newsContainer.style.display = 'block';
    displayNews(allNews);
  } else {
    document.getElementById('filter').style.display = 'none';
    newsContainer.style.display = 'none';
    document.getElementById(currentTab).style.display = 'block';
  }
}

function showFilteredNews(keyword) {
  const filtered = {};
  for (const date in allNews) {
    filtered[date] = allNews[date].filter(n => n.title.includes(keyword));
  }
  displayNews(filtered);
}

function displayNews(data) {
  newsContainer.innerHTML = '';
  const dates = Object.keys(data).sort((a, b) => b.localeCompare(a));
  dates.forEach(date => {
    const section = document.createElement('div');
    section.innerHTML = `<h3>📅 ${date}</h3>`;
    data[date].forEach(item => {
      const div = document.createElement('div');
      div.className = 'news-item';
      div.innerHTML = `
        <a href="${item.link}" target="_blank">📰 ${item.title}</a>
        <button class="delete-btn" data-date="${date}" data-title="${item.title}">🗑️</button>
      `;
      section.appendChild(div);
    });
    newsContainer.appendChild(section);
  });

  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const date = btn.dataset.date;
      const title = btn.dataset.title;
      fetch('https://novaticker-api.onrender.com/delete_news', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({date, title})
      }).then(() => {
        btn.parentElement.remove();
      });
    });
  });
}

function loadData() {
  fetch('https://novaticker-api.onrender.com/data.json')
    .then(res => res.json())
    .then(data => {
      const rising = document.getElementById('rising');
      const signal = document.getElementById('signal');
      rising.innerHTML = '';
      signal.innerHTML = '';
      allNews = data.positive_news;

      data.rising.forEach(item => {
        rising.innerHTML += formatItem(item);
      });
      data.signal.forEach(item => {
        signal.innerHTML += formatItem(item);
      });

      if (currentTab === 'news') {
        displayNews(allNews);
      }

      lastUpdated.textContent = `🕒 마지막 갱신: 불러오는 중...`;
      setTimeout(() => {
        const now = new Date();
        lastUpdated.textContent = `🕒 마지막 갱신: ${now.toLocaleString()}`;
      }, 300);
    });
}

function formatItem(item) {
  const newsPart = item.news ? `⭐ <a href="${item.news.link}" target="_blank">${item.news.title}</a>` : '';
  return `<div>📈 ${item.symbol} (${item.change}% ↑) ${newsPart}</div>`;
}

loadData();
setInterval(loadData, 180000); // 3분마다 갱신
