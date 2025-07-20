document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".tab");
  const sections = document.querySelectorAll(".section");
  const filterButtons = document.querySelectorAll(".filter-btn");
  const resetButton = document.getElementById("reset-btn");

  let rawData = {};

  function switchTab(tabId) {
    tabs.forEach(tab => tab.classList.remove("active"));
    sections.forEach(section => section.classList.remove("active"));

    document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add("active");
    document.getElementById(tabId).classList.add("active");
  }

  tabs.forEach(tab => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });

  resetButton.addEventListener("click", () => renderNews(rawData.positive_news));

  filterButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const type = btn.dataset.type;
      const filtered = {};
      for (const date in rawData.positive_news) {
        filtered[date] = rawData.positive_news[date].filter(n =>
          n.title.includes(type)
        );
      }
      renderNews(filtered);
    });
  });

  function deleteNews(date, title) {
    fetch("https://novatickerapp.onrender.com/delete_news", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date, title })
    }).then(() => fetchData());
  }

  function renderNews(data) {
    const newsContainer = document.getElementById("news-container");
    newsContainer.innerHTML = "";
    const sortedDates = Object.keys(data).sort((a, b) => b.localeCompare(a));

    sortedDates.forEach(date => {
      const title = document.createElement("h3");
      title.textContent = `🗓 ${date}`;
      newsContainer.appendChild(title);

      data[date].forEach(n => {
        const div = document.createElement("div");
        div.className = "news-item";
        div.innerHTML = `
          <a href="${n.link}" target="_blank">${n.title}</a>
          <button class="delete-btn">🗑️</button>
        `;
        div.querySelector("button").onclick = () => deleteNews(date, n.title);
        newsContainer.appendChild(div);
      });
    });
  }

  function renderStock(list, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";
    list.forEach(s => {
      const div = document.createElement("div");
      div.className = "stock-item";
      const star = s.news ? "⭐" : "";
      const link = s.news ? `<a href="${s.news.link}" target="_blank">${s.news.title}</a>` : "";
      div.innerHTML = `
        <div>📈 ${s.symbol} ${star}</div>
        <div>📊 ${s.change}% | 거래량 ${s.volume.toLocaleString()}</div>
        ${link ? `<div class="news-link">${link}</div>` : ""}
      `;
      container.appendChild(div);
    });
  }

  function fetchData() {
    fetch("https://novatickerapp.onrender.com/data.json")
      .then(res => res.json())
      .then(data => {
        rawData = data;
        renderNews(data.positive_news);
        renderStock(data.rising, "rising-list");
        renderStock(data.signal, "signal-list");
        document.getElementById("loading").style.display = "none";
      })
      .catch(e => {
        console.error("데이터 로딩 실패:", e);
      });
  }

  fetchData();
});
