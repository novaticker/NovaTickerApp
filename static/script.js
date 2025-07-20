function openTab(evt, tabName) {
  let tabcontent = document.getElementsByClassName("tabcontent");
  let tablinks = document.getElementsByClassName("tablinks");
  for (let i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  for (let i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove("active");
  }
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.classList.add("active");
}

async function loadRisingStocks() {
  try {
    let res = await fetch("/rising_stocks.json");
    let data = await res.json();
    let html = "";

    if (data.results.length === 0) {
      html = "📭 급등 종목 없음";
    } else {
      data.results.forEach(item => {
        html += `<div class="card">
          <b>${item.ticker}</b> (${item.percent}%)<br/>
          💵 ${item.open} → ${item.latest}<br/>
          🔥 거래량: ${item.volume_now.toLocaleString()} (평균 ${item.volume_prev.toLocaleString()})<br/>`;

        if (item.news && item.news.length > 0) {
          html += `📰 관련 뉴스:<br/>`;
          item.news.forEach(n => {
            html += `<a href="${n.link}" target="_blank">- ${n.title}</a><br/>`;
          });
        }

        html += `</div>`;
      });
    }

    document.getElementById("stocksArea").innerHTML = html;
    if (data.updated) {
      document.getElementById("stocksTime").innerText = "⏰ 마지막 갱신: " + data.updated;
    }
  } catch (err) {
    document.getElementById("stocksArea").innerHTML = "❌ 오류 발생";
  }
}

async function loadPositiveNews() {
  try {
    let res = await fetch("/positive_news.json");
    let data = await res.json();
    let html = "";

    let updatedText = "";

    if (data.updated) {
      updatedText = data.updated;
      delete data.updated;
    } else {
      updatedText = Object.keys(data).sort().reverse()[0] || "정보 없음";
    }

    document.getElementById("newsTime").innerText = "⏰ 마지막 갱신: " + updatedText;

    if (Object.keys(data).length === 0) {
      html = "📭 뉴스 없음";
    } else {
      const dates = Object.keys(data).sort().reverse();
      dates.forEach(date => {
        html += `<div class="date-title">📅 ${date}</div>`;
        data[date].forEach(item => {
          html += `<div class="card">
            <a href="${item.link}" target="_blank">${item.title}</a><br/>
            🔑 ${item.keyword || ""}</div>`;
        });
      });
    }

    document.getElementById("newsArea").innerHTML = html;
  } catch (err) {
    document.getElementById("newsArea").innerHTML = "❌ 뉴스 불러오기 실패";
  }
}

// 최초 실행
loadRisingStocks();
loadPositiveNews();

// 5분마다 자동 새로고침
setInterval(() => {
  loadRisingStocks();
  loadPositiveNews();
}, 5 * 60 * 1000);
