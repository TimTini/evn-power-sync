const SCHEDULE_URL = "data/schedule.json";

const generatedAtEl = document.getElementById("generated-at");
const dateRangeEl = document.getElementById("date-range");
const eventCountEl = document.getElementById("event-count");
const metaPanelEl = document.getElementById("meta-panel");
const statusEl = document.getElementById("status");
const eventsEl = document.getElementById("events");
const searchInputEl = document.getElementById("search-input");

let allEvents = [];

function formatDateTime(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
}

function formatSource(source) {
  if (source === "evnhcmc") {
    return "EVNHCMC";
  }
  if (source === "evnspc") {
    return "EVNSPC";
  }
  return source || "EVN";
}

function locationLine(event) {
  const parts = [event.province, event.district_or_company, event.ward].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
}

function foldText(value) {
  return (value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function renderEvents(events) {
  eventsEl.innerHTML = "";

  if (!events.length) {
    statusEl.textContent = "Không có lịch trong khoảng ngày đã chọn.";
    statusEl.classList.remove("error");
    return;
  }

  statusEl.textContent = `Hiển thị ${events.length} sự kiện.`;
  statusEl.classList.remove("error");

  for (const event of events) {
    const card = document.createElement("article");
    card.className = "event-card";

    const badge = document.createElement("div");
    badge.className = "badge";
    badge.textContent = formatSource(event.source);

    const title = document.createElement("h2");
    title.textContent = event.area || "Khu vực chưa rõ";

    const meta = document.createElement("div");
    meta.className = "event-meta";

    const time = document.createElement("p");
    time.textContent = `Thời gian: ${formatDateTime(event.start_at)} → ${formatDateTime(event.end_at)}`;
    meta.appendChild(time);

    const location = locationLine(event);
    if (location) {
      const locationEl = document.createElement("p");
      locationEl.textContent = `Vị trí: ${location}`;
      meta.appendChild(locationEl);
    }

    if (Array.isArray(event.stations) && event.stations.length) {
      const stationsEl = document.createElement("p");
      stationsEl.textContent = `Trạm: ${event.stations.join(", ")}`;
      meta.appendChild(stationsEl);
    }

    const reason = document.createElement("p");
    reason.textContent = `Lý do: ${event.reason || "—"}`;
    meta.appendChild(reason);

    card.appendChild(badge);
    card.appendChild(title);
    card.appendChild(meta);
    eventsEl.appendChild(card);
  }
}

function applyFilter() {
  const needle = foldText(searchInputEl.value.trim());
  if (!needle) {
    renderEvents(allEvents);
    return;
  }

  const filtered = allEvents.filter((event) => {
    const haystack = foldText(
      [event.area, event.reason, event.province, event.district_or_company, event.ward, ...(event.stations || [])].join(" "),
    );
    return haystack.includes(needle);
  });
  renderEvents(filtered);
}

async function loadSchedule() {
  try {
    const response = await fetch(`${SCHEDULE_URL}?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    allEvents = Array.isArray(payload.events) ? payload.events : [];

    generatedAtEl.textContent = payload.generated_at ? formatDateTime(payload.generated_at) : "Chưa có";
    dateRangeEl.textContent =
      payload.from_date && payload.to_date ? `${payload.from_date} → ${payload.to_date}` : "—";
    eventCountEl.textContent = String(allEvents.length);
    metaPanelEl.hidden = false;

    if (!payload.generated_at) {
      statusEl.textContent = "Chưa có lần sync nào. Chờ GitHub Actions chạy lần đầu hoặc export thủ công.";
      statusEl.classList.remove("error");
      eventsEl.innerHTML = "";
      return;
    }

    applyFilter();
  } catch (error) {
    statusEl.textContent = `Không tải được ${SCHEDULE_URL}: ${error.message}`;
    statusEl.classList.add("error");
    eventsEl.innerHTML = "";
  }
}

searchInputEl.addEventListener("input", applyFilter);
loadSchedule();
