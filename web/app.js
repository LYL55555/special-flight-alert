const config = window.SPECIAL_FLIGHT_CONFIG || {};

function resolveApiBaseUrls() {
  const urls = [];
  const host = window.location.hostname;
  const isLocal = host === "localhost" || host === "127.0.0.1";

  if (isLocal) {
    if (config.localApiBaseUrl) {
      urls.push(String(config.localApiBaseUrl).replace(/\/$/, ""));
    }
    for (const port of [8000, 8001, 8002, 8003]) {
      urls.push(`http://127.0.0.1:${port}`);
    }
  }
  if (config.tunnelApiBaseUrl) {
    urls.push(String(config.tunnelApiBaseUrl).replace(/\/$/, ""));
  }
  if (config.apiBaseUrl) {
    urls.push(String(config.apiBaseUrl).replace(/\/$/, ""));
  }

  return [...new Set(urls.filter(Boolean))];
}

const API_BASE_URLS = resolveApiBaseUrls();
const API_BASE_URL = API_BASE_URLS[0] || "http://127.0.0.1:8000";

const AIRPORTS = [
  { code: "PVD", name: "Rhode Island T. F. Green International", city: "Providence", region: "Rhode Island, United States", aliases: ["tf green", "providence"] },
  { code: "BOS", name: "Boston Logan International", city: "Boston", region: "Massachusetts, United States", aliases: ["logan"] },
  { code: "BDL", name: "Bradley International", city: "Hartford", region: "Connecticut, United States", aliases: ["bradley"] },
  { code: "JFK", name: "John F. Kennedy International", city: "New York", region: "New York, United States", aliases: ["kennedy"] },
  { code: "LGA", name: "LaGuardia", city: "New York", region: "New York, United States", aliases: ["laguardia"] },
  { code: "EWR", name: "Newark Liberty International", city: "Newark", region: "New Jersey, United States", aliases: ["newark"] },
  { code: "PHL", name: "Philadelphia International", city: "Philadelphia", region: "Pennsylvania, United States", aliases: ["philly"] },
  { code: "IAD", name: "Washington Dulles International", city: "Washington", region: "Virginia, United States", aliases: ["dulles"] },
  { code: "DCA", name: "Ronald Reagan Washington National", city: "Washington", region: "District of Columbia, United States", aliases: ["reagan"] },
  { code: "MIA", name: "Miami International", city: "Miami", region: "Florida, United States", aliases: [] },
  { code: "FLL", name: "Fort Lauderdale-Hollywood International", city: "Fort Lauderdale", region: "Florida, United States", aliases: ["fort lauderdale"] },
  { code: "MCO", name: "Orlando International", city: "Orlando", region: "Florida, United States", aliases: [] },
  { code: "ATL", name: "Hartsfield-Jackson Atlanta International", city: "Atlanta", region: "Georgia, United States", aliases: ["hartsfield"] },
  { code: "ORD", name: "O'Hare International", city: "Chicago", region: "Illinois, United States", aliases: ["ohare", "o'hare"] },
  { code: "DFW", name: "Dallas Fort Worth International", city: "Dallas", region: "Texas, United States", aliases: ["fort worth"] },
  { code: "DEN", name: "Denver International", city: "Denver", region: "Colorado, United States", aliases: [] },
  { code: "LAX", name: "Los Angeles International", city: "Los Angeles", region: "California, United States", aliases: [] },
  { code: "SFO", name: "San Francisco International", city: "San Francisco", region: "California, United States", aliases: [] },
  { code: "SEA", name: "Seattle-Tacoma International", city: "Seattle", region: "Washington, United States", aliases: ["seatac", "sea tac"] },
  { code: "XIY", name: "Xi'an Xianyang International", city: "Xi'an", region: "Shaanxi, China", aliases: ["xian", "xi an", "xianyang", "西安", "咸阳"] },
  { code: "PEK", name: "Beijing Capital International", city: "Beijing", region: "Beijing, China", aliases: ["beijing", "capital", "北京", "首都机场"] },
  { code: "PKX", name: "Beijing Daxing International", city: "Beijing", region: "Beijing, China", aliases: ["beijing", "daxing", "北京", "大兴机场"] },
  { code: "PVG", name: "Shanghai Pudong International", city: "Shanghai", region: "Shanghai, China", aliases: ["shanghai", "pudong", "上海", "浦东"] },
  { code: "SHA", name: "Shanghai Hongqiao International", city: "Shanghai", region: "Shanghai, China", aliases: ["shanghai", "hongqiao", "上海", "虹桥"] },
  { code: "CAN", name: "Guangzhou Baiyun International", city: "Guangzhou", region: "Guangdong, China", aliases: ["guangzhou", "canton", "广州", "白云"] },
  { code: "SZX", name: "Shenzhen Bao'an International", city: "Shenzhen", region: "Guangdong, China", aliases: ["shenzhen", "baoan", "深圳", "宝安"] },
  { code: "CTU", name: "Chengdu Shuangliu International", city: "Chengdu", region: "Sichuan, China", aliases: ["chengdu", "shuangliu", "成都", "双流"] },
  { code: "TFU", name: "Chengdu Tianfu International", city: "Chengdu", region: "Sichuan, China", aliases: ["chengdu", "tianfu", "成都", "天府"] },
  { code: "CKG", name: "Chongqing Jiangbei International", city: "Chongqing", region: "Chongqing, China", aliases: ["chongqing", "重庆", "江北"] },
  { code: "HGH", name: "Hangzhou Xiaoshan International", city: "Hangzhou", region: "Zhejiang, China", aliases: ["hangzhou", "杭州", "萧山"] },
  { code: "NKG", name: "Nanjing Lukou International", city: "Nanjing", region: "Jiangsu, China", aliases: ["nanjing", "南京", "禄口"] },
  { code: "TAO", name: "Qingdao Jiaodong International", city: "Qingdao", region: "Shandong, China", aliases: ["qingdao", "青岛", "胶东"] },
  { code: "XMN", name: "Xiamen Gaoqi International", city: "Xiamen", region: "Fujian, China", aliases: ["xiamen", "厦门", "高崎"] },
];

const COPY = {
  en: {
    brand: "Special Flight Watch",
    headline: "Find unusual aircraft near an airport.",
    airportLabel: "Airport or city",
    scanButton: "Search",
    scanHint: "Search by city, airport name, or 3-letter airport code.",
    statusLabel: "Status",
    statusReady: "Ready",
    statusSearching: "Searching",
    statusComplete: "Complete",
    statusCached: "Cached",
    statusError: "Error",
    statusInvalid: "Invalid",
    matchesLabel: "Matches",
    sourceLabel: "Data",
    boardEyebrow: "Current Board",
    noScanTitle: "No search yet",
    showLabel: "Show",
    allFlights: "All",
    arrivals: "Arrivals",
    departures: "Departures",
    airlineLabel: "Airline",
    allAirlines: "All airlines",
    sortLabel: "Sort",
    sortTimeAsc: "Time early-late",
    sortTimeDesc: "Time late-early",
    sortAirlineAsc: "Airline A-Z",
    sortAirlineDesc: "Airline Z-A",
    sortAircraftAsc: "Aircraft A-Z",
    sortAircraftDesc: "Aircraft Z-A",
    sortRegAsc: "Registration A-Z",
    sortRegDesc: "Registration Z-A",
    emptyState: "Search for an airport to see unusual aircraft, special liveries, and rare types.",
    searchingTitle: "Searching {airport}",
    searchingBody: "Checking upcoming flights. This can take a few seconds.",
    noMatches: "No flights match the current filter.",
    airportNeeded: "Choose an airport",
    airportNeededBody: "Type a city, airport name, or airport code, then choose one of the suggestions.",
    searchErrorBody: "Could not search this airport right now. Check the airport code or choose one from the suggestions.",
    degradedBody: "Live flight data is temporarily unavailable. Please try again later.",
    statusDegraded: "Unavailable",
    unavailableTitle: "{airport} search unavailable",
    fallbackUnknown: "Unknown",
    fallbackNoReg: "No registration",
    fallbackNoPhoto: "No photo found",
    unnumberedFlight: "Flight",
    sourceSchedule: "Schedule",
    sourceLive: "Live",
    labelArrival: "Arrival",
    labelDeparture: "Departure",
    labelTime: "Time",
    timePending: "Time pending",
    details: "Details",
    scheduledDeparture: "Scheduled departure",
    estimatedDeparture: "Estimated departure",
    scheduledArrival: "Scheduled arrival",
    estimatedArrival: "Estimated arrival",
    whyListed: "Why listed",
    photos: "Photos",
    registration: "Registration",
    aircraft: "Aircraft",
    airline: "Airline",
    movement: "Direction",
    specialLivery: "Special livery",
    rareAircraft: "Rare aircraft",
    listedBecause: "Listed because it matched this watch list.",
  },
  zh: {
    brand: "特殊航班观察",
    headline: "查找机场附近值得拍的特殊飞机。",
    airportLabel: "机场或城市",
    scanButton: "搜索",
    scanHint: "可以输入城市、机场名，或三字机场码。",
    statusLabel: "状态",
    statusReady: "待搜索",
    statusSearching: "搜索中",
    statusComplete: "完成",
    statusCached: "缓存",
    statusError: "错误",
    statusInvalid: "无效",
    matchesLabel: "结果",
    sourceLabel: "数据",
    boardEyebrow: "当前列表",
    noScanTitle: "还没有搜索",
    showLabel: "显示",
    allFlights: "全部",
    arrivals: "到达",
    departures: "出发",
    airlineLabel: "航司",
    allAirlines: "全部航司",
    sortLabel: "排序",
    sortTimeAsc: "时间从早到晚",
    sortTimeDesc: "时间从晚到早",
    sortAirlineAsc: "航司 A-Z",
    sortAirlineDesc: "航司 Z-A",
    sortAircraftAsc: "机型 A-Z",
    sortAircraftDesc: "机型 Z-A",
    sortRegAsc: "注册号 A-Z",
    sortRegDesc: "注册号 Z-A",
    emptyState: "搜索机场后，可以看到特殊涂装、稀有机型和其他值得关注的飞机。",
    searchingTitle: "正在搜索 {airport}",
    searchingBody: "正在检查未来航班，通常需要几秒钟。",
    noMatches: "当前筛选条件下没有结果。",
    airportNeeded: "请选择机场",
    airportNeededBody: "输入城市、机场名或机场码，然后从提示里选择机场。",
    searchErrorBody: "暂时无法搜索这个机场。请检查机场码，或从提示里选择一个机场。",
    degradedBody: "实时航班数据暂时不可用，请稍后再试。",
    statusDegraded: "不可用",
    unavailableTitle: "{airport} 暂时无法搜索",
    fallbackUnknown: "未知",
    fallbackNoReg: "暂无注册号",
    fallbackNoPhoto: "暂无照片",
    unnumberedFlight: "航班",
    sourceSchedule: "计划航班",
    sourceLive: "实时",
    labelArrival: "到达",
    labelDeparture: "出发",
    labelTime: "时间",
    timePending: "时间待定",
    details: "详情",
    scheduledDeparture: "计划出发",
    estimatedDeparture: "预计出发",
    scheduledArrival: "计划到达",
    estimatedArrival: "预计到达",
    whyListed: "入选原因",
    photos: "照片",
    registration: "注册号",
    aircraft: "机型",
    airline: "航司",
    movement: "方向",
    specialLivery: "特殊涂装",
    rareAircraft: "稀有机型",
    listedBecause: "因为命中了观察规则。",
  },
};

const form = document.querySelector("#scanForm");
const input = document.querySelector("#airportInput");
const button = document.querySelector("#scanButton");
const languageToggle = document.querySelector("#languageToggle");
const suggestions = document.querySelector("#airportSuggestions");
const scopeAirport = document.querySelector("#scopeAirport");
const statusText = document.querySelector("#statusText");
const countText = document.querySelector("#countText");
const sourceText = document.querySelector("#sourceText");
const resultTitle = document.querySelector("#resultTitle");
const queryTime = document.querySelector("#queryTime");
const movementFilter = document.querySelector("#movementFilter");
const airlineFilter = document.querySelector("#airlineFilter");
const sortMode = document.querySelector("#sortMode");
const emptyState = document.querySelector("#emptyState");
const resultsList = document.querySelector("#resultsList");
const template = document.querySelector("#flightCardTemplate");

const airportPattern = /^[A-Za-z]{3,4}$/;
let currentPayload = null;
let currentLanguage = "en";

function t(key, params = {}) {
  let value = COPY[currentLanguage][key] || COPY.en[key] || key;
  Object.entries(params).forEach(([name, replacement]) => {
    value = value.replace(`{${name}}`, replacement);
  });
  return value;
}

function applyLanguage() {
  document.documentElement.lang = currentLanguage === "zh" ? "zh-Hans" : "en";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  input.placeholder = currentLanguage === "zh"
    ? "试试 Providence、Boston、Xi'an、西安 或 PVD"
    : "Try Providence, Boston, Xi'an, or PVD";
  languageToggle.textContent = currentLanguage === "zh" ? "English" : "中文";
  if (!currentPayload) {
    statusText.textContent = t("statusReady");
    resultTitle.textContent = t("noScanTitle");
  } else {
    renderFlights(currentPayload, { preserveFilters: true });
  }
  renderSuggestions();
}

function setBusy(isBusy) {
  button.disabled = isBusy;
  input.disabled = isBusy;
  document.body.classList.toggle("is-scanning", isBusy);
}

function setStatus(text, tone = "neutral") {
  statusText.textContent = text;
  statusText.dataset.tone = tone;
}

function clean(value, fallback = "Unknown") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function normalizeSearchText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[’']/g, "")
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, " ");
}

function findAirport(value) {
  const term = normalizeSearchText(value);
  if (!term) return null;
  return AIRPORTS.find((airport) => {
    const searchable = [
      airport.code,
      airport.city,
      airport.name,
      airport.region,
      ...airport.aliases,
    ].map(normalizeSearchText);
    return (
      searchable.some((item) => item === term) ||
      searchable.some((item) => item.replace(/\s+/g, "") === term.replace(/\s+/g, ""))
    );
  });
}

function matchingAirports(value) {
  const term = normalizeSearchText(value);
  if (!term) return AIRPORTS.slice(0, 5);
  return AIRPORTS.filter((airport) => {
    const searchable = [
      airport.code,
      airport.city,
      airport.name,
      airport.region,
      ...airport.aliases,
    ].map(normalizeSearchText);
    const compactTerm = term.replace(/\s+/g, "");
    return searchable.some((item) => {
      return item.includes(term) || item.replace(/\s+/g, "").includes(compactTerm);
    });
  }).slice(0, 7);
}

function resolveAirportCode(value) {
  const trimmed = value.trim();
  const airport = findAirport(trimmed);
  if (airport) return airport.code;
  if (airportPattern.test(trimmed)) return trimmed.toUpperCase();
  return null;
}

function renderSuggestions() {
  const matches = matchingAirports(input.value);
  suggestions.innerHTML = "";
  suggestions.hidden = matches.length === 0;
  matches.forEach((airport) => {
    const buttonEl = document.createElement("button");
    buttonEl.type = "button";
    buttonEl.className = "suggestion-row";
    buttonEl.innerHTML = `
      <span class="suggestion-main">
        <strong>${airport.name}</strong>
        <small>${airport.city} · ${airport.region}</small>
      </span>
      <span class="suggestion-code">${airport.code}</span>
    `;
    buttonEl.addEventListener("click", () => {
      input.value = airport.code;
      scopeAirport.textContent = airport.code;
      suggestions.hidden = true;
      input.focus();
    });
    suggestions.append(buttonEl);
  });
}

function formatQueryTime(payload) {
  if (!payload.queried_at) return "";
  const date = new Date(payload.queried_at);
  if (Number.isNaN(date.getTime())) return payload.queried_at;
  return date.toLocaleString(currentLanguage === "zh" ? "zh-CN" : undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatShortDateTime(value) {
  if (!value) return "";
  const match = String(value).match(
    /^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})(?::\d{2})?\s*(?:\(([^)]+)\))?$/
  );
  if (!match) return String(value).replace(/^\d{4}-/, "");

  const [, , monthRaw, dayRaw, hourRaw, minuteRaw, tzRaw] = match;
  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const month = monthNames[Number(monthRaw) - 1] || monthRaw;
  const day = String(Number(dayRaw));
  const hour24 = Number(hourRaw);
  const suffix = hour24 >= 12 ? "PM" : "AM";
  const hour12 = hour24 % 12 || 12;
  const tz = tzRaw ? ` ${tzRaw}` : "";
  if (currentLanguage === "zh") {
    const period = hour24 >= 12 ? "下午" : "上午";
    return `${Number(monthRaw)}月${Number(dayRaw)}日 ${period}${hour12}:${minuteRaw}${tz}`;
  }
  return `${month} ${day}, ${hour12}:${minuteRaw} ${suffix}${tz}`;
}

function formatCompactDateTime(value) {
  const full = formatShortDateTime(value);
  return full.replace(/^([A-Z][a-z]{2})\s+(\d+),\s+/, "$1 $2 ");
}

function parseTime(value) {
  if (!value) return Number.POSITIVE_INFINITY;
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? Number.POSITIVE_INFINITY : time;
}

function primaryTime(flight) {
  const movement = clean(flight.movement, "").toLowerCase();
  if (flight.primary_time || flight.primary_time_local) {
    return {
      label: clean(flight.primary_time_label, movement || "time"),
      display: formatCompactDateTime(flight.primary_time_local) || t("timePending"),
      sort: parseTime(flight.primary_time),
    };
  }
  if (movement === "departure") {
    return {
      label: "departure",
      display:
        formatCompactDateTime(flight.estimated_departure_local || flight.scheduled_departure_local) ||
        t("timePending"),
      sort: parseTime(flight.estimated_departure || flight.scheduled_departure),
    };
  }
  if (movement === "arrival") {
    return {
      label: "arrival",
      display:
        formatCompactDateTime(flight.estimated_arrival_local || flight.scheduled_arrival_local) ||
        t("timePending"),
      sort: parseTime(flight.estimated_arrival || flight.scheduled_arrival),
    };
  }
  return {
    label: "time",
    display:
      formatCompactDateTime(
        flight.estimated_departure_local ||
          flight.scheduled_departure_local ||
          flight.estimated_arrival_local ||
          flight.scheduled_arrival_local
      ) ||
      t("timePending"),
    sort: parseTime(
      flight.estimated_departure ||
        flight.scheduled_departure ||
        flight.estimated_arrival ||
        flight.scheduled_arrival
    ),
  };
}

function routeEndpoint(flight, key) {
  if (key === "origin") return clean(flight.origin, "----");
  return clean(flight.destination, "----");
}

function matchTitle(flight) {
  const reasons = flight.reasons || [];
  const livery = flight.livery_name || flight.livery_airline;
  const type = flight.aircraft_type;
  const military = reasons.find((reason) => /military|operator/i.test(reason));
  const rare = reasons.find((reason) => /rare|A380|A388|B747|B74|C-?17|C5|AN/i.test(reason));
  const special = reasons.find((reason) => /livery/i.test(reason));

  if (livery) return `${t("specialLivery")}: ${livery}`;
  if (rare && type) return `${t("rareAircraft")}: ${type}`;
  if (military) return military;
  if (special) return special;
  if (type) return `${t("rareAircraft")}: ${type}`;
  return reasons[0] || "Rule match";
}

function matchDescription(flight) {
  const reasons = flight.reasons || [];
  const title = matchTitle(flight).toLowerCase();
  if (flight.livery_description && flight.livery_description.toLowerCase() !== title) {
    return flight.livery_description;
  }
  const uniqueReasons = [...new Set(reasons)].filter((reason) => {
    return reason && reason.toLowerCase() !== title;
  });
  if (uniqueReasons.length > 0) return uniqueReasons.join(", ");
  return "";
}

function setActionLink(link, url) {
  if (url) {
    link.href = url;
    link.hidden = false;
    link.removeAttribute("aria-disabled");
  } else {
    link.hidden = true;
    link.removeAttribute("href");
    link.setAttribute("aria-disabled", "true");
  }
}

function normalizeAirlineName(value) {
  let name = clean(value, "").trim();
  if (!name) return "";
  name = name.replace(/\s*\([^)]*\)\s*/g, " ").replace(/\s+/g, " ").trim();

  const lower = name.toLowerCase();
  const aliases = [
    [/^jetblue\b|jet blue/, "JetBlue"],
    [/^american airlines\b|^american\b/, "American Airlines"],
    [/^delta air lines\b|^delta\b/, "Delta Air Lines"],
    [/^united airlines\b|^united\b/, "United Airlines"],
    [/^southwest airlines\b|^southwest\b/, "Southwest Airlines"],
    [/^alaska airlines\b|^alaska\b/, "Alaska Airlines"],
    [/^spirit airlines\b|^spirit\b/, "Spirit Airlines"],
    [/^frontier airlines\b|^frontier\b/, "Frontier Airlines"],
    [/^breeze airways\b|^breeze\b/, "Breeze Airways"],
  ];
  const match = aliases.find(([pattern]) => pattern.test(lower));
  return match ? match[1] : name;
}

function decorateMedia(card, flight) {
  const img = card.querySelector("img");
  const media = card.querySelector(".aircraft-media");
  const credit = card.querySelector(".photo-credit");
  const fallback = card.querySelector(".aircraft-fallback");
  const imageUrl = flight.image_url || flight.photo_url || flight.links?.image;

  const photoTarget = flight.links?.jetphotos || flight.jetphotos_url || flight.photo_page_url || flight.links?.planespotters;
  if (photoTarget) {
    media.href = photoTarget;
    media.removeAttribute("aria-disabled");
  } else {
    media.removeAttribute("href");
    media.setAttribute("aria-disabled", "true");
  }
  card.querySelector(".fallback-type").textContent = clean(flight.aircraft_type, t("aircraft"));
  card.querySelector(".fallback-reg").textContent = `${clean(flight.registration, t("fallbackNoReg"))} · ${t("fallbackNoPhoto")}`;

  if (!imageUrl) {
    media.hidden = false;
    img.hidden = true;
    credit.hidden = true;
    fallback.hidden = false;
    return;
  }

  media.hidden = false;
  credit.textContent = "";
  credit.hidden = true;
  img.src = imageUrl;
  img.alt = `${clean(flight.registration, "Aircraft")} photo`;
  img.hidden = false;
  fallback.hidden = true;
  img.addEventListener("error", () => {
    media.hidden = false;
    img.hidden = true;
    credit.hidden = true;
    fallback.hidden = false;
  });
}

function operatorKey(flight) {
  return flight.operator_display || normalizeAirlineName(flight.operator || flight.airline_icao);
}

function registrationKey(flight) {
  return clean(flight.registration, "").trim();
}

function aircraftKey(flight) {
  return clean(flight.aircraft_type, "").trim();
}

function updateAirlineFilter(payload) {
  const previous = airlineFilter.value;
  const airlines = [...new Set((payload.flights || []).map(operatorKey).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b));

  airlineFilter.innerHTML = "";
  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = t("allAirlines");
  airlineFilter.append(allOption);
  airlines.forEach((airline) => {
    const option = document.createElement("option");
    option.value = airline;
    option.textContent = airline;
    airlineFilter.append(option);
  });

  if (previous && [...airlineFilter.options].some((option) => option.value === previous)) {
    airlineFilter.value = previous;
  }
}

function withSharedImages(flights) {
  const imagesByRegistration = new Map();
  flights.forEach((flight) => {
    const reg = registrationKey(flight).toUpperCase();
    const image = flight.image_url || flight.photo_url;
    if (reg && image && !imagesByRegistration.has(reg)) {
      imagesByRegistration.set(reg, image);
    }
  });
  return flights.map((flight) => {
    const reg = registrationKey(flight).toUpperCase();
    const sharedImage = reg ? imagesByRegistration.get(reg) : null;
    if (!sharedImage || flight.image_url || flight.photo_url) return flight;
    return { ...flight, image_url: sharedImage, photo_url: sharedImage };
  });
}

function filteredAndSortedFlights(payload) {
  const selectedMovement = movementFilter.value;
  const selectedAirline = airlineFilter.value;
  const selectedSort = sortMode.value;
  const airport = payload.airport;

  return withSharedImages(payload.flights || [])
    .map((flight) => ({
      ...flight,
      origin: flight.display_origin || flight.origin || (flight.movement === "departure" ? airport : null),
      destination: flight.display_destination || flight.destination || (flight.movement === "arrival" ? airport : null),
      _primaryTime: primaryTime(flight),
    }))
    .filter((flight) => selectedMovement === "all" || flight.movement === selectedMovement)
    .filter((flight) => selectedAirline === "all" || operatorKey(flight) === selectedAirline)
    .sort((a, b) => {
      if (selectedSort === "time-desc") return b._primaryTime.sort - a._primaryTime.sort;
      if (selectedSort === "airline-asc") {
        return operatorKey(a).localeCompare(operatorKey(b));
      }
      if (selectedSort === "airline-desc") {
        return operatorKey(b).localeCompare(operatorKey(a));
      }
      if (selectedSort === "type-asc") {
        return aircraftKey(a).localeCompare(aircraftKey(b));
      }
      if (selectedSort === "type-desc") {
        return aircraftKey(b).localeCompare(aircraftKey(a));
      }
      if (selectedSort === "registration-asc") {
        return registrationKey(a).localeCompare(registrationKey(b));
      }
      if (selectedSort === "registration-desc") {
        return registrationKey(b).localeCompare(registrationKey(a));
      }
      return a._primaryTime.sort - b._primaryTime.sort;
    });
}

function renderFlights(payload, options = {}) {
  currentPayload = payload;
  updateAirlineFilter(payload);
  resultsList.innerHTML = "";

  if (payload.status === "degraded") {
    countText.textContent = "0";
    sourceText.textContent = payload.source === "fallback" ? t("statusDegraded") : t("statusError");
    resultTitle.textContent = t("unavailableTitle", { airport: payload.airport });
    queryTime.textContent = "";
    emptyState.hidden = false;
    emptyState.querySelector("p").textContent = payload.message || t("degradedBody");
    return;
  }

  const flights = filteredAndSortedFlights(payload);

  countText.textContent = String(flights.length);
  sourceText.textContent = payload.cached ? `${t("statusCached")} ${payload.cache_age_seconds}s` : "FR24";
  resultTitle.textContent = currentLanguage === "zh"
    ? `${payload.airport} 特殊航班`
    : `${payload.airport} watch list`;
  queryTime.textContent = formatQueryTime(payload);
  emptyState.hidden = flights.length > 0;

  if (flights.length === 0) {
    emptyState.querySelector("p").textContent = t("noMatches");
    return;
  }

  flights.forEach((flight, index) => {
    const card = template.content.firstElementChild.cloneNode(true);
    card.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n);
    });
    const time = flight._primaryTime;
    card.style.setProperty("--delay", `${index * 70}ms`);
    decorateMedia(card, flight);
    const sourceLabel = flight.source === "schedule" ? t("sourceSchedule") : t("sourceLive");
    card.querySelector(".flight-kicker").textContent = sourceLabel.toUpperCase();
    card.querySelector("h3").textContent = clean(flight.flight_number, t("unnumberedFlight"));
    const timeLabelKey = `label${time.label.charAt(0).toUpperCase()}${time.label.slice(1)}`;
    card.querySelector(".time-label").textContent = t(timeLabelKey);
    card.querySelector(".primary-time").textContent = time.display;
    card.querySelector(".origin").textContent = routeEndpoint(flight, "origin");
    card.querySelector(".destination").textContent = routeEndpoint(flight, "destination");
    card.querySelector(".registration").textContent = clean(flight.registration, t("fallbackUnknown"));
    card.querySelector(".aircraft-type").textContent = clean(flight.aircraft_type, t("fallbackUnknown"));
    card.querySelector(".operator").textContent = clean(flight.operator_display || flight.operator, t("fallbackUnknown"));
    card.querySelector(".movement").textContent = flight.movement === "arrival" ? t("arrivals") : flight.movement === "departure" ? t("departures") : clean(flight.movement, t("fallbackUnknown"));

    card.querySelector(".livery-chip").textContent = matchTitle(flight);
    const description = matchDescription(flight);
    card.querySelector(".livery-description").textContent = description;
    card.querySelector(".livery-description").hidden = !description;

    card.querySelector(".scheduled-departure").textContent = clean(
      formatShortDateTime(flight.scheduled_departure_local)
    );
    card.querySelector(".estimated-departure").textContent = clean(
      formatShortDateTime(flight.estimated_departure_local)
    );
    card.querySelector(".scheduled-arrival").textContent = clean(
      formatShortDateTime(flight.scheduled_arrival_local)
    );
    card.querySelector(".estimated-arrival").textContent = clean(
      formatShortDateTime(flight.estimated_arrival_local)
    );
    card.querySelector(".reasons").textContent = matchTitle(flight);

    setActionLink(card.querySelector(".fr24-link"), flight.links?.fr24);
    setActionLink(
      card.querySelector(".photo-link"),
      flight.links?.jetphotos || flight.jetphotos_url || flight.photo_page_url || flight.links?.planespotters
    );

    resultsList.append(card);
  });
}

async function fetchScanPayload(airport) {
  const errors = [];
  for (let i = 0; i < API_BASE_URLS.length; i += 1) {
    const base = API_BASE_URLS[i];
    const hasFallback = i < API_BASE_URLS.length - 1;
    try {
      const response = await fetch(`${base}/api/scan?airport=${encodeURIComponent(airport)}`);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        errors.push(`${base}: HTTP ${response.status}`);
        continue;
      }
      if (payload.status === "degraded" && hasFallback) {
        errors.push(`${base}: live data unavailable`);
        continue;
      }
      return { payload, base };
    } catch (error) {
      errors.push(`${base}: ${error.message || "network error"}`);
    }
  }
  throw new Error(errors.join(" · ") || t("searchErrorBody"));
}

async function scanAirport(airport) {
  setBusy(true);
  currentPayload = null;
  resultsList.innerHTML = "";
  setStatus(t("statusSearching"), "working");
  countText.textContent = "--";
  sourceText.textContent = "FR24";
  resultTitle.textContent = t("searchingTitle", { airport });
  queryTime.textContent = "";
  emptyState.hidden = false;
  emptyState.querySelector("p").textContent = t("searchingBody");

  try {
    const { payload, base } = await fetchScanPayload(airport);
    sourceText.textContent = base.includes("127.0.0.1") || base.includes("localhost")
      ? "Local"
      : base.includes("trycloudflare.com")
        ? "Tunnel"
        : payload.cached
          ? `${t("statusCached")} ${payload.cache_age_seconds}s`
          : "FR24";

    renderFlights(payload);
    if (payload.status === "degraded") {
      setStatus(t("statusDegraded"), "bad");
    } else {
      setStatus(payload.cached ? t("statusCached") : t("statusComplete"), payload.cached ? "cached" : "good");
    }
  } catch (error) {
    currentPayload = null;
    resultsList.innerHTML = "";
    countText.textContent = "--";
    sourceText.textContent = t("statusError");
    resultTitle.textContent = t("unavailableTitle", { airport });
    queryTime.textContent = "";
    emptyState.hidden = false;
    emptyState.querySelector("p").textContent = error.message || t("searchErrorBody");
    setStatus(t("statusError"), "bad");
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const airport = resolveAirportCode(input.value);

  if (!airport) {
    setStatus(t("statusInvalid"), "bad");
    currentPayload = null;
    resultsList.innerHTML = "";
    resultTitle.textContent = t("airportNeeded");
    emptyState.hidden = false;
    emptyState.querySelector("p").textContent = t("airportNeededBody");
    renderSuggestions();
    return;
  }

  input.value = airport;
  scopeAirport.textContent = airport;
  suggestions.hidden = true;
  scanAirport(airport);
});

input.addEventListener("input", () => {
  const airport = resolveAirportCode(input.value);
  scopeAirport.textContent = airport || input.value.trim().slice(0, 4).toUpperCase() || "---";
  renderSuggestions();
});

movementFilter.addEventListener("change", () => {
  if (currentPayload) renderFlights(currentPayload);
});

airlineFilter.addEventListener("change", () => {
  if (currentPayload) renderFlights(currentPayload);
});

sortMode.addEventListener("change", () => {
  if (currentPayload) renderFlights(currentPayload);
});

languageToggle.addEventListener("click", () => {
  currentLanguage = currentLanguage === "zh" ? "en" : "zh";
  applyLanguage();
});

applyLanguage();
