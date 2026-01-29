document.addEventListener("DOMContentLoaded", () => {
  const data = window.__DASH_DATA__ || null;

  const rentEl = document.getElementById("rentChart");
  const expEl = document.getElementById("expenseChart");
  const occEl = document.getElementById("occupancyChart");

  const labels = data?.labels || ["Aug","Sep","Oct","Nov","Dec","Jan"];
  const rentVals = data?.rent || [14000,16500,17800,19000,20000,21500];
  const expVals = data?.expenses || [6200,7100,6800,7900,8400,8200];
  const occVals = data?.occupancy || [19,4];

  if (rentEl) {
    new Chart(rentEl, {
      type: "line",
      data: { labels, datasets: [{ label: "Rent Collected (ZMW)", data: rentVals, tension: 0.35, fill: true }] },
      options: { responsive: true }
    });
  }

  if (expEl) {
    new Chart(expEl, {
      type: "bar",
      data: { labels, datasets: [{ label: "Expenses (ZMW)", data: expVals }] },
      options: { responsive: true }
    });
  }

  if (occEl) {
    new Chart(occEl, {
      type: "doughnut",
      data: { labels: ["Occupied", "Available"], datasets: [{ data: occVals }] },
      options: { responsive: true }
    });
  }
});
