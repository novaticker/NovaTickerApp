// 탭 전환
document.querySelectorAll(".tab-button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    const tab = btn.getAttribute("data-tab");
    document.querySelectorAll(".section").forEach(sec => sec.classList.add("hidden"));
    document.getElementById(`${tab}-section`).classList.remove("hidden");
  });
});

// 급등 종목 로드
fetch("/rising_stocks.json")
  .then(res => res.json())
  .then(data => {
    const list = document.getElementById("rising-list");
    const lastUpdated = document.getElementById("last-updated");
    if (data.length === 0) {
      list.innerHTML = "<li>📯 감지된 종목 없음</li>";
    } else {
      data.forEach(item => {
        const li = document.createElement("li");
        const star = item.news ? " ⭐" : "";
        li.textContent = `${item.ticker}${star} - ${item.reason}`;
        if (item.news) {
          const newsLink = document.createElement("a");
          newsLink.href = item.news.link;
          newsLink.textContent = ` 🔗 ${item.news.title}`;
          newsLink.target = "_blank";
          li.appendChild(document.createElement("br"));
          li.appendChild(newsLink);
        }
        list.appendChild(li);
      });
    }
    lastUpdated.textContent = data.length ? data[0].timestamp : "정보 없음";
  });

// 급등 조짐 종목 로드
fetch("/preparing_stocks.json")
  .then(res => res.json())
  .then(data => {
    const list = document.getElementById("preparing-list");
    const lastUpdated = document.getElementById("last-updated-pre");
    if (data.length === 0) {
      list.innerHTML = "<li>📯 감지된 종목 없음</li>";
    } else {
      data.forEach(item => {
        const li = document.createElement("li");
        const star = item.news ? " ⭐" : "";
        li.textContent = `${item.ticker}${star} - ${item.reason}`;
        if (item.news) {
          const newsLink = document.createElement("a");
          newsLink.href = item.news.link;
          newsLink.textContent = ` 🔗 ${item.news.title}`;
          newsLink.target = "_blank";
          li.appendChild(document.createElement("br"));
          li.appendChild(newsLink);
        }
        list.appendChild(li);
      });
    }
    lastUpdated.textContent = data.length ? data[0].timestamp : "정보 없음";
  });

// 뉴스 불러오기
let originalNewsData = {};

fetch("/positive_news.json")
  .then(res => res.json())
  .then(news => {
    originalNewsData = news;
    displayNews(news);
  });

function displayNews(newsData) {
  const container = document.getElementById("news-list");
  container.innerHTML = "";
  Object.keys(newsData).reverse().forEach(date => {
    const dateBox = document.createElement("div");
    dateBox.innerHTML = `<h3>🗓️ ${date}</h3>`;
    newsData[date].forEach((n, idx) => {
      const item = document.createElement("div");
      item.className = "news-item";
      const title = document.createElement("a");
      title.href = n.link;
      title.target = "_blank";
      title.innerText = "📰 " + n.title;
      const delBtn = document.createElement("button");
      delBtn.innerText = "🗑️";
      delBtn.className = "delete-btn";
      delBtn.onclick = () => {
        fetch(`/delete_news?date=${date}&index=${idx}`).then(() => {
          location.reload();
        });
      };
      item.appendChild(title);
      item.appendChild(delBtn);
      item.setAttribute("data-title", n.title.toLowerCase());
      dateBox.appendChild(item);
    });
    container.appendChild(dateBox);
  });
}

// 필터 버튼 기능
document.querySelectorAll(".filter-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const type = btn.dataset.type;
    const newsList = document.querySelectorAll(".news-item");

    if (btn.classList.contains("reset")) {
      newsList.forEach(n => n.style.display = "block");
      return;
    }

    newsList.forEach(n => {
      const title = n.getAttribute("data-title");
      if (
        (type === "fda" && /fda|임상|clinical/.test(title)) ||
        (type === "bio" && /바이오|제약|헬스케어/.test(title)) ||
        (type === "rebound" && /반등|급락 후/.test(title)) ||
        (type === "soaring" && /급등|폭등|상한가/.test(title))
      ) {
        n.style.display = "block";
      } else {
        n.style.display = "none";
      }
    });
  });
});
