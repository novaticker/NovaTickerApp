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
          <b>${item.ticker}</b> (${item.percent}
