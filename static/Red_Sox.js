function sortTable(n) {
  var table = document.getElementById("rosterTable");
  var switching = true;
  var dir = "asc";
  var switchcount = 0;

  while (switching) {
    switching = false;
    var rows = table.rows;

    for (var i = 1; i < rows.length - 1; i++) {
      var shouldSwitch = false;
      var xCell = rows[i].getElementsByTagName("TD")[n];
      var yCell = rows[i + 1].getElementsByTagName("TD")[n];

      var x = xCell.getAttribute("data-sort") || xCell.innerText;
      var y = yCell.getAttribute("data-sort") || yCell.innerText;

      x = x.toLowerCase();
      y = y.toLowerCase();

      if (dir === "asc" && x > y) {
        shouldSwitch = true;
        break;
      }
      if (dir === "desc" && x < y) {
        shouldSwitch = true;
        break;
      }
    }

    if (shouldSwitch) {
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      switchcount++;
    } else {
      if (switchcount === 0 && dir === "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}
let currentDate = document.querySelector("#currentDate");
const date = new Date();
currentDate.textContent = date.toLocaleString("en-US", {
  timeZone: "America/Chicago",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

async function loadSched() {
  try {
    const res = await fetch("/api/redsox_sched");
    if (!res.ok) throw new Error("Network response was not ok");
    const data = await res.json();

    let tbody = document.querySelector("#summary thead");
    tbody.innerHTML = "";

    let gameDate = document.querySelector("#gameDate");
    const date = new Date(data.date);
    gameDate.textContent = date.toLocaleString("en-US", {
      timeZone: "America/Chicago",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });

    let fragment = document.createDocumentFragment();
    let tr = document.createElement("tr");

    // Status cell
    const statusTh = document.createElement("th");
    statusTh.textContent = data.gameStatus;
    tr.appendChild(statusTh);

    // Inning cells
    for (const r of data.gameInnings) {
      const th = document.createElement("th");
      th.textContent = r;
      tr.appendChild(th);
    }
    // R, H, E cells
    const rTh = document.createElement("th");
    rTh.textContent = "R";
    rTh.className = "EHR-table-right EHR-table-left";
    tr.appendChild(rTh);

    const hTh = document.createElement("th");
    hTh.textContent = "H";
    hTh.className = "EHR-table-right EHR-table-left";
    tr.appendChild(hTh);

    const eTh = document.createElement("th");
    eTh.textContent = "E";
    eTh.className = "EHR-table-right EHR-table-left";
    tr.appendChild(eTh);

    fragment.appendChild(tr);
    tbody.appendChild(fragment);

    tbody = document.querySelector("#summary tbody");
    tbody.innerHTML = "";

    fragment = document.createDocumentFragment();
    tr = document.createElement("tr");

    // Away team row
    const awayTeamTd = document.createElement("td");
    awayTeamTd.textContent = data.teams.away.name;
    awayTeamTd.className = "left";
    tr.appendChild(awayTeamTd);

    // Inning cells
    for (const r of data.teams.away.innings) {
      const td = document.createElement("td");
      td.textContent = r;
      tr.appendChild(td);
    }

    // R, H, E cells
    const awayRTd = document.createElement("td");
    awayRTd.textContent = data.teams.away.R;
    awayRTd.className = "EHR-table-right EHR-table-left";
    tr.appendChild(awayRTd);

    const awayHTd = document.createElement("td");
    awayHTd.textContent = data.teams.away.H;
    awayHTd.className = "EHR-table-right EHR-table-left";
    tr.appendChild(awayHTd);

    const awayETd = document.createElement("td");
    awayETd.textContent = data.teams.away.E;
    awayETd.className = "EHR-table-right EHR-table-left";

    tr.appendChild(awayETd);

    fragment.appendChild(tr);
    tbody.appendChild(fragment);

    fragment = document.createDocumentFragment();
    tr = document.createElement("tr");

    // Home team row
    const homeTeamTd = document.createElement("td");
    homeTeamTd.textContent = data.teams.home.name;
    homeTeamTd.className = "left";
    tr.appendChild(homeTeamTd);

    // Inning cells
    for (const r of data.teams.home.innings) {
      const th = document.createElement("th");
      th.textContent = r;
      tr.appendChild(th);
    }

    // R, H, E cells
    const homeRTd = document.createElement("td");
    homeRTd.textContent = data.teams.home.R;
    homeRTd.className = "EHR-table-right EHR-table-left";
    tr.appendChild(homeRTd);

    const homeHTd = document.createElement("td");
    homeHTd.textContent = data.teams.home.H;
    homeHTd.className = "EHR-table-right EHR-table-left";
    tr.appendChild(homeHTd);

    const homeETd = document.createElement("td");
    homeETd.textContent = data.teams.home.E;
    homeETd.className = "EHR-table-right EHR-table-left";
    tr.appendChild(homeETd);

    fragment.appendChild(tr);
    tbody.appendChild(fragment);

    fragment = document.createDocumentFragment();
    tr = document.createElement("tr");

    document.getElementById("status").style.display = "none";
    document.getElementById("summary").style.display = "block";
  } catch (err) {
    document.getElementById("status").textContent = "Error loading stats.";
    console.error(err);
  }
}

async function loadStandings() {
  try {
    const res = await fetch("/api/redsox_standings");
    if (!res.ok) throw new Error("Network response was not ok");
    const records = await res.json();

    const tbody = document.querySelector("#standings tbody");
    tbody.innerHTML = "";

    // Guard clause for empty data
    if (!Array.isArray(records) || records.length === 0) {
      tbody.innerHTML = `
    <tr>
      <td colspan="9" class="center">No standings data available.</td>
    </tr>
  `;
      document.getElementById("status").style.display = "none";
      document.getElementById("standings").style.display = "block";
      return;
    }

    // Build rows efficiently
    const fragment = document.createDocumentFragment();

    for (const r of records) {
      const tr = document.createElement("tr");

      tr.innerHTML = `
    <td>${r.rank}</td>
    <td class="left">${r.team}</td>
    <td>${r.wins}</td>
    <td>${r.losses}</td>
    <td>${r.gb}</td>
    <td>${r.elim}</td>
    <td>${r.wc_rank}</td>
    <td>${r.wc_gb}</td>
    <td>${r.wc_elim}</td>
  `;

      fragment.appendChild(tr);
    }

    tbody.appendChild(fragment);

    document.getElementById("status").style.display = "none";
    document.getElementById("standings").style.display = "block";
  } catch (err) {
    document.getElementById("status").textContent = "Error loading stats.";
    console.error(err);
  }
}

async function loadTransactions() {
  try {
    const res = await fetch("/api/redsox_transactions");
    if (!res.ok) throw new Error("Network response was not ok");
    const records = await res.json();

    const tbody = document.querySelector("#transactions tbody");
    tbody.innerHTML = "";

    // Guard clause for empty data
    if (!Array.isArray(records) || records.length === 0) {
      tbody.innerHTML = `
    <tr>
      <td colspan="9" class="center">No transactions data available.</td>
    </tr>
  `;
      document.getElementById("status").style.display = "none";
      document.getElementById("transactions").style.display = "block";
      return;
    }
    // Build rows efficiently
    const fragment = document.createDocumentFragment();

    for (const r of records) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
                    <td>${r.date}</td>
                    <td class="left">${r.description}</td>
                    <td><a href='${r.formatted_link}' target='_blank'>${r.player}</a></td>
                `;
      fragment.appendChild(tr);
    }

    tbody.appendChild(fragment);

    document.getElementById("status").style.display = "none";
    document.getElementById("transactions").style.display = "block";
  } catch (err) {
    document.getElementById("status").textContent = "Error loading stats.";
    console.error(err);
  }
}

async function loadRoster() {
  try {
    const res = await fetch("/api/redsox_roster");
    if (!res.ok) throw new Error("Network response was not ok");
    const records = await res.json();

    const tbody = document.querySelector("#roster tbody");
    tbody.innerHTML = "";

    for (const r of records) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
                    <td data-sort="${r.sortName}" class="left"><a href='${r.formatted_link}' target='_blank'>${r.name}</a></td>
                    <td class="left">${r.position}</td>
                    <td>${r.number}</td>
                `;
      tbody.appendChild(tr);
    }
    sortTable(0); // Initial sort by Name

    document.getElementById("status").style.display = "none";
    document.getElementById("roster").style.display = "block";
  } catch (err) {
    document.getElementById("status").textContent = "Error loading stats.";
    console.error(err);
  }
}

// Load once on page load

loadStandings();
loadTransactions();
loadRoster();
loadSched();
