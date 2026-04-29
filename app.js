const DATA_URL = "./data/latest.json";
const MANIFEST_URL = "./data/manifest.json";
const SHARD_URLS = {
  players: "./data/players.json",
  live: "./data/live.json",
  schedule: "./data/schedule.json",
  training: "./data/training.json",
  draws: "./data/draws.json"
};
const VIEW_STORAGE_KEY = "madrid-open-active-view";
const SIDEBAR_STORAGE_KEYS = {
  players: "madrid-open-sidebar-players",
  courts: "madrid-open-sidebar-courts"
};
const SELECTION_STORAGE_KEYS = {
  player: "madrid-open-active-player",
  court: "madrid-open-active-court"
};

const state = {
  data: null,
  filteredPlayers: [],
  activePlayerId: getStoredSelection("player"),
  activeCourtId: getStoredSelection("court"),
  activeView: getStoredView(),
  sidebarCollapsed: {
    players: getStoredSidebarState("players"),
    courts: getStoredSidebarState("courts")
  },
  query: ""
};

const statusLabels = {
  F: "已结束",
  O: "进行中",
  L: "进行中",
  P: "进行中",
  C: "已取消",
  S: "未开赛",
  U: "待排赛程"
};
const LIVE_MATCH_TIME_LABEL = "正在进行";

const entryTypeLabels = {
  LL: "LL 幸运落败者",
  Q: "Q 资格赛晋级",
  WC: "WC 外卡",
  ALT: "ALT 替补",
  PR: "PR 保护排名",
  SE: "SE 特别豁免"
};

const courtAliases = {
  "MANOLO SANTANA STADIUM": "Court 1",
  "ARANTXA SANCHEZ STADIUM": "Court 2",
  "STADIUM 3": "Court 3",
  "MANOLO SANTANA": "Court 1",
  "ARANTXA SANCHEZ": "Court 2",
  "ESTADIO 3": "Court 3"
};

const countryZhNames = {
  AND: "安道尔",
  ARG: "阿根廷",
  ARM: "亚美尼亚",
  AUS: "澳大利亚",
  AUT: "奥地利",
  BEL: "比利时",
  BIH: "波黑",
  BLR: "白俄罗斯",
  BRA: "巴西",
  BUL: "保加利亚",
  CAN: "加拿大",
  CHI: "智利",
  CHN: "中国",
  COL: "哥伦比亚",
  CRO: "克罗地亚",
  CZE: "捷克",
  DEN: "丹麦",
  ESP: "西班牙",
  FIN: "芬兰",
  FRA: "法国",
  GBR: "英国",
  GEO: "格鲁吉亚",
  GER: "德国",
  GRE: "希腊",
  HUN: "匈牙利",
  INA: "印度尼西亚",
  IND: "印度",
  ITA: "意大利",
  JPN: "日本",
  KAZ: "哈萨克斯坦",
  LAT: "拉脱维亚",
  LTU: "立陶宛",
  LUX: "卢森堡",
  MEX: "墨西哥",
  MON: "摩纳哥",
  NED: "荷兰",
  NOR: "挪威",
  NZL: "新西兰",
  PAR: "巴拉圭",
  PER: "秘鲁",
  PHI: "菲律宾",
  POL: "波兰",
  POR: "葡萄牙",
  ROU: "罗马尼亚",
  RSA: "南非",
  RUS: "俄罗斯",
  SLO: "斯洛文尼亚",
  SRB: "塞尔维亚",
  SUI: "瑞士",
  SVK: "斯洛伐克",
  SWE: "瑞典",
  TPE: "中国台北",
  TUN: "突尼斯",
  TUR: "土耳其",
  UKR: "乌克兰",
  USA: "美国",
  UZB: "乌兹别克斯坦"
};

const dom = {
  refreshStatus: document.querySelector("#refreshStatus"),
  reloadBtn: document.querySelector("#reloadBtn"),
  viewSwitch: document.querySelector("#viewSwitch"),
  playersView: document.querySelector("#playersView"),
  courtsView: document.querySelector("#courtsView"),
  playersSidebar: document.querySelector("#playersSidebar"),
  courtsSidebar: document.querySelector("#courtsSidebar"),
  playersSidebarToggle: document.querySelector("#playersSidebarToggle"),
  courtsSidebarToggle: document.querySelector("#courtsSidebarToggle"),
  playersSidebarExpand: document.querySelector("#playersSidebarExpand"),
  courtsSidebarExpand: document.querySelector("#courtsSidebarExpand"),
  playerSearch: document.querySelector("#playerSearch"),
  playerSearchClear: document.querySelector("#playerSearchClear"),
  playerList: document.querySelector("#playerList"),
  emptyState: document.querySelector("#emptyState"),
  playerDetail: document.querySelector("#playerDetail"),
  doublesSection: document.querySelector("#doublesSection"),
  playerTopline: document.querySelector("#playerTopline"),
  playerName: document.querySelector("#playerName"),
  playerIdentity: document.querySelector("#playerIdentity"),
  matchSplit: document.querySelector("#matchSplit"),
  matchCount: document.querySelector("#matchCount"),
  trainingCount: document.querySelector("#trainingCount"),
  singlesMatchRows: document.querySelector("#singlesMatchRows"),
  doublesMatchRows: document.querySelector("#doublesMatchRows"),
  matchRows: document.querySelector("#matchRows"),
  trainingRows: document.querySelector("#trainingRows"),
  courtList: document.querySelector("#courtList"),
  courtEmptyState: document.querySelector("#courtEmptyState"),
  courtDetail: document.querySelector("#courtDetail"),
  courtName: document.querySelector("#courtName"),
  courtMeta: document.querySelector("#courtMeta"),
  courtMatchCount: document.querySelector("#courtMatchCount"),
  courtDayCount: document.querySelector("#courtDayCount"),
  courtDaySections: document.querySelector("#courtDaySections")
};

boot();

function boot() {
  bindSidebarControls("players");
  bindSidebarControls("courts");
  window.setInterval(refreshCurrentCourtActivity, 60_000);

  if (dom.reloadBtn) {
    dom.reloadBtn.addEventListener("click", () => {
      loadData(true);
    });
  }

  if (dom.playerSearch) {
    dom.playerSearch.addEventListener("input", (event) => {
      applyPlayerSearch(event.target.value);
    });

    dom.playerSearch.addEventListener("search", () => {
      dom.playerSearch.blur();
    });

    dom.playerSearch.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        dom.playerSearch.blur();
      }
    });
  }

  if (dom.playerSearchClear) {
    dom.playerSearchClear.addEventListener("click", () => {
      if (!dom.playerSearch) {
        return;
      }
      dom.playerSearch.value = "";
      applyPlayerSearch("");
      dom.playerSearch.blur();
    });
  }

  if (dom.viewSwitch) {
    dom.viewSwitch.addEventListener("click", (event) => {
      const target = event.target.closest("[data-view]");
      if (!target) {
        return;
      }

      const view = target.getAttribute("data-view") || "players";
      if (view !== "players" && view !== "courts") {
        return;
      }

      state.activeView = view;
      renderView();
    });
  }

  if (dom.playerDetail) {
    dom.playerDetail.addEventListener("click", (event) => {
      const playerTarget = event.target.closest("[data-player-id]");
      if (playerTarget) {
        event.preventDefault();
        const playerId = playerTarget.getAttribute("data-player-id") || "";
        openPlayer(playerId);
        return;
      }

      const courtTarget = event.target.closest("[data-court-id]");
      if (!courtTarget) {
        return;
      }

      event.preventDefault();
      const courtId = courtTarget.getAttribute("data-court-id") || "";
      openCourt(courtId);
    });
  }

  if (dom.courtList) {
    dom.courtList.addEventListener("click", (event) => {
      const target = event.target.closest("[data-court-id]");
      if (!target) {
        return;
      }

      event.preventDefault();
      const courtId = target.getAttribute("data-court-id") || "";
      openCourt(courtId);
    });
  }

  if (dom.courtDetail) {
    dom.courtDetail.addEventListener("click", (event) => {
      const playerTarget = event.target.closest("[data-player-id]");
      if (playerTarget) {
        event.preventDefault();
        const playerId = playerTarget.getAttribute("data-player-id") || "";
        openPlayer(playerId);
        return;
      }

      const courtTarget = event.target.closest("[data-court-id]");
      if (!courtTarget) {
        return;
      }

      event.preventDefault();
      const courtId = courtTarget.getAttribute("data-court-id") || "";
      openCourt(courtId);
    });
  }

  loadData();
  renderSidebarState();
}

function bindSidebarControls(view) {
  const toggle = dom[`${view}SidebarToggle`];
  const expand = dom[`${view}SidebarExpand`];

  if (toggle) {
    toggle.addEventListener("click", () => {
      setSidebarCollapsed(view, true);
    });
  }

  if (expand) {
    expand.addEventListener("click", () => {
      setSidebarCollapsed(view, false);
    });
  }
}

function applyPlayerSearch(value) {
  state.query = String(value || "").trim();
  renderPlayerSearchClear();
  filterPlayers();
  renderPlayerList();

  if (!state.filteredPlayers.some((player) => player.id === state.activePlayerId)) {
    state.activePlayerId = state.filteredPlayers[0]?.id ?? null;
    storeActiveSelection("player", state.activePlayerId);
    renderDetail();
  }
}

function renderPlayerSearchClear() {
  if (dom.playerSearchClear) {
    dom.playerSearchClear.hidden = !state.query;
  }
}

async function loadData(force = false) {
  setStatus("数据加载中");

  try {
    const payload = await loadCurrentPayload(force);
    state.data = normalizePayload(payload);

    if (!state.activePlayerId || !state.data.playerById[state.activePlayerId]) {
      state.activePlayerId = state.data.players[0]?.id ?? null;
      storeActiveSelection("player", state.activePlayerId);
    }
    if (!state.activeCourtId || !state.data.courtById[state.activeCourtId]) {
      state.activeCourtId = state.data.courts[0]?.id ?? null;
      storeActiveSelection("court", state.activeCourtId);
    }

    filterPlayers();
    renderPlayerList();
    renderDetail();
    renderCourtList();
    renderCourtDetail();
    renderView();

    setStatus(formatRefreshStatus(state.data.metadata));
  } catch (error) {
    setStatus(`加载失败：${error.message}`);
    setHtml(dom.playerList, `<p class="card-sub">无法加载数据文件（${DATA_URL}）。</p>`);
    setHtml(dom.courtList, `<p class="card-sub">无法加载场地数据。</p>`);
    setHidden(dom.emptyState, false);
    setHidden(dom.playerDetail, true);
    setHidden(dom.courtEmptyState, false);
    setHidden(dom.courtDetail, true);
  }
}

async function loadCurrentPayload(force = false) {
  try {
    return await loadShardedPayload(force);
  } catch (error) {
    console.warn("Falling back to compatibility snapshot", error);
    return loadLegacyPayload(force);
  }
}

async function loadLegacyPayload(force = false) {
  return fetchJson(DATA_URL, force);
}

async function loadShardedPayload(force = false) {
  const manifest = await fetchJson(MANIFEST_URL, force);
  const tracks = manifest?.tracks || {};

  const [
    playersShard,
    liveShard,
    scheduleShard,
    trainingShard,
    drawsShard
  ] = await Promise.all([
    fetchJson(getTrackUrl(tracks, "players"), force),
    fetchJson(getTrackUrl(tracks, "live"), force),
    fetchJson(getTrackUrl(tracks, "schedule"), force),
    fetchJson(getTrackUrl(tracks, "training"), force),
    fetchJson(getTrackUrl(tracks, "draws"), force)
  ]);

  return combineShardedPayload({
    manifest,
    playersShard,
    liveShard,
    scheduleShard,
    trainingShard,
    drawsShard
  });
}

async function fetchJson(url, force = false) {
  const requestUrl = withCacheBust(url, force);
  const response = await fetch(requestUrl, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`数据请求失败：HTTP ${response.status}`);
  }

  return response.json();
}

function withCacheBust(url, force = false) {
  if (!force) {
    return url;
  }

  const separator = String(url).includes("?") ? "&" : "?";
  return `${url}${separator}ts=${Date.now()}`;
}

function getTrackUrl(tracks, name) {
  return tracks?.[name]?.path || SHARD_URLS[name];
}

function combineShardedPayload({
  manifest,
  playersShard,
  liveShard,
  scheduleShard,
  trainingShard,
  drawsShard
}) {
  const tracks = manifest?.tracks || {};
  const metadata = {
    ...(manifest?.metadata || {}),
    tracks,
    sources: {
      ...(playersShard?.metadata?.sources || {}),
      ...(liveShard?.metadata?.sources || {}),
      ...(scheduleShard?.metadata?.sources || {}),
      ...(trainingShard?.metadata?.sources || {}),
      ...(drawsShard?.metadata?.sources || {})
    },
    playerRankingDate: playersShard?.metadata?.playerRankingDate || "",
    trainingDays: trainingShard?.metadata?.trainingDays || [],
    audit: {
      ...(playersShard?.metadata?.audit || {}),
      ...(drawsShard?.metadata?.audit || {})
    }
  };

  if (!metadata.updatedAt) {
    metadata.updatedAt = getLatestTrackUpdatedAt(tracks);
  }

  return {
    metadata,
    players: Array.isArray(playersShard?.players) ? playersShard.players : [],
    matches: mergeShardedMatches(
      scheduleShard?.matches,
      liveShard?.matches,
      drawsShard?.matches
    ),
    trainingSessions: Array.isArray(trainingShard?.trainingSessions) ? trainingShard.trainingSessions : []
  };
}

function mergeShardedMatches(scheduleMatches, liveMatches, drawMatches) {
  const byId = new Map();

  addMatchRecords(byId, Array.isArray(scheduleMatches) ? scheduleMatches : []);
  addMatchRecords(byId, Array.isArray(liveMatches) ? liveMatches : []);

  const existingSignatures = new Set(
    [...byId.values()]
      .map(matchRosterSignature)
      .filter(Boolean)
  );

  (Array.isArray(drawMatches) ? drawMatches : []).forEach((match) => {
    const id = String(match?.id || "").trim();
    const signature = matchRosterSignature(match);

    if (id && byId.has(id)) {
      mergeMatchRecord(byId.get(id), match);
      return;
    }
    if (signature && existingSignatures.has(signature)) {
      return;
    }
    if (id) {
      byId.set(id, { ...match });
      if (signature) {
        existingSignatures.add(signature);
      }
    }
  });

  return [...byId.values()];
}

function addMatchRecords(byId, matches) {
  matches.forEach((match) => {
    const id = String(match?.id || "").trim();
    if (!id) {
      return;
    }

    if (!byId.has(id)) {
      byId.set(id, { ...match });
      return;
    }

    mergeMatchRecord(byId.get(id), match);
  });
}

function mergeMatchRecord(target, source) {
  Object.entries(source || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    if (Array.isArray(value) && value.length === 0) {
      return;
    }
    target[key] = value;
  });
}

function matchRosterSignature(match) {
  const players = Array.isArray(match?.players) ? match.players : [];
  if (!players.length || getMatchDisplayDiscipline(match) !== "doubles") {
    return "";
  }

  const sideA = players
    .filter((player) => String(player?.side || "").toUpperCase() === "A")
    .map((player) => String(player?.id || "").trim())
    .filter(Boolean)
    .sort();
  const sideB = players
    .filter((player) => String(player?.side || "").toUpperCase() === "B")
    .map((player) => String(player?.id || "").trim())
    .filter(Boolean)
    .sort();

  if (!sideA.length || !sideB.length) {
    return "";
  }

  return [sideA.join("+"), sideB.join("+")].sort().join("|");
}

function getLatestTrackUpdatedAt(tracks) {
  return Object.values(tracks || {})
    .map((track) => String(track?.updatedAt || ""))
    .filter(Boolean)
    .sort()
    .pop() || "";
}

function formatRefreshStatus(metadata) {
  const tracks = metadata?.tracks || {};
  if (tracks.live || tracks.schedule || tracks.training || tracks.players) {
    const parts = [
      formatTrackStatusPart("比分", tracks.live),
      formatTrackStatusPart("赛程", tracks.schedule),
      formatTrackStatusPart("训练", tracks.training),
      formatTrackStatusPart("球员", tracks.players)
    ].filter(Boolean);
    return `更新：${parts.join(" / ")}`;
  }

  const updatedAt = formatDateTime(metadata?.updatedAt);
  return `快照时间：${updatedAt}，10-20min数据刷新`;
}

function formatTrackStatusPart(label, track) {
  if (!track?.updatedAt) {
    return "";
  }
  return `${label} ${formatDateTime(track.updatedAt)}`;
}

function normalizePayload(payload) {
  const players = Array.isArray(payload.players) ? payload.players : [];
  const matches = Array.isArray(payload.matches) ? payload.matches : [];
  const trainingSessions = Array.isArray(payload.trainingSessions) ? payload.trainingSessions : [];

  const singlesByPlayer = createBucket(matches.filter((match) => match.discipline === "singles"));
  const doublesByPlayer = createBucket(matches.filter((match) => match.discipline === "doubles"));
  const trainingByPlayer = createBucket(trainingSessions);
  const matchesByCourt = createCourtBucket(matches);
  const trainingByCourt = createCourtBucket(trainingSessions);

  const enrichedPlayers = players
    .map((player) => {
      const singlesItems = singlesByPlayer[player.id] || [];
      const doublesItems = doublesByPlayer[player.id] || [];
      const singlesCount = singlesItems.length;
      const doublesCount = doublesItems.length;
      const matchItems = [...singlesItems, ...doublesItems];
      const totalMatchCount = matchItems.length;
      const singlesOpenCount = singlesItems.filter((match) => !isFinishedMatch(match.status)).length;
      const trainingCount = trainingByPlayer[player.id]?.length ?? 0;
      const singlesEliminated = isDisciplineEliminated(player, singlesItems);
      const doublesEliminated = isDisciplineEliminated(player, doublesItems);
      const singlesEntryType = getPlayerSinglesEntryType(player, singlesItems);
      const enteredDisciplines = [singlesCount > 0, doublesCount > 0].filter(Boolean).length;
      const overallEliminated = enteredDisciplines > 0 && [
        singlesCount === 0 || singlesEliminated,
        doublesCount === 0 || doublesEliminated
      ].every(Boolean);

      return {
        ...player,
        singlesCount,
        singlesOpenCount,
        doublesCount,
        totalMatchCount,
        trainingCount,
        totalCount: totalMatchCount + trainingCount,
        singlesEntryType,
        singlesEliminated,
        doublesEliminated,
        overallEliminated
      };
    })
    .sort((a, b) => {
      return (
        Number(a.overallEliminated) - Number(b.overallEliminated) ||
        compareRanking(a, b) ||
        b.totalMatchCount - a.totalMatchCount ||
        b.trainingCount - a.trainingCount ||
        a.name.localeCompare(b.name)
      );
    });

  const playerById = {};
  enrichedPlayers.forEach((player) => {
    playerById[player.id] = player;
  });

  const allCourtIds = new Set([...Object.keys(matchesByCourt), ...Object.keys(trainingByCourt)]);
  const courts = [...allCourtIds]
    .map((id) => {
      const courtMatches = matchesByCourt[id] || [];
      const courtTraining = trainingByCourt[id] || [];
      const days = new Set(
        [...courtMatches.map((match) => getCourtDayKey(match)), ...courtTraining.map((session) => getTrainingDayKey(session))]
          .filter(Boolean)
      );

      return {
        id,
        name: id,
        matchCount: courtMatches.length,
        trainingCount: courtTraining.length,
        currentTrainingCount: courtTraining.filter((session) => isCurrentTrainingSession(session)).length,
        liveCount: courtMatches.filter((match) => isLiveMatchStatus(match.status)).length,
        openCount: courtMatches.filter((match) => !isFinishedMatch(match.status)).length,
        todayOpenCount: courtMatches.filter((match) => (
          !isFinishedMatch(match.status) && getCourtDayKey(match) === getTodayCourtDayKey()
        )).length,
        dayCount: days.size
      };
    })
    .sort((a, b) => compareCourtName(a.name, b.name));

  const courtActivity = summarizeCourtActivity(courts);

  const courtById = {};
  courts.forEach((court) => {
    courtById[court.id] = court;
  });

  return {
    metadata: payload.metadata ?? {},
    players: enrichedPlayers,
    playerById,
    singlesByPlayer,
    doublesByPlayer,
    trainingByPlayer,
    matchesByCourt,
    trainingByCourt,
    courts,
    courtById,
    courtActivity
  };
}

function refreshCurrentCourtActivity() {
  if (!state.data?.courts?.length) {
    return;
  }

  let changed = false;
  state.data.courts.forEach((court) => {
    const training = state.data.trainingByCourt?.[court.id] || [];
    const currentTrainingCount = training.filter((session) => isCurrentTrainingSession(session)).length;
    if (court.currentTrainingCount !== currentTrainingCount) {
      changed = true;
      court.currentTrainingCount = currentTrainingCount;
    }
  });
  const courtActivity = summarizeCourtActivity(state.data.courts);
  if (
    state.data.courtActivity?.liveMatchCourtCount !== courtActivity.liveMatchCourtCount ||
    state.data.courtActivity?.currentTrainingCourtCount !== courtActivity.currentTrainingCourtCount
  ) {
    changed = true;
    state.data.courtActivity = courtActivity;
  }

  if (!changed) {
    return;
  }

  const courtListScrollTop = dom.courtList?.scrollTop ?? 0;
  renderCourtList();
  if (dom.courtList) {
    dom.courtList.scrollTop = courtListScrollTop;
  }
  renderCourtDetail();
  renderView();
}

function summarizeCourtActivity(courts) {
  return {
    liveMatchCourtCount: courts.filter((court) => court.liveCount > 0).length,
    currentTrainingCourtCount: courts.filter((court) => court.currentTrainingCount > 0).length
  };
}

function createBucket(items) {
  const map = {};

  items.forEach((item) => {
    const players = Array.isArray(item.players) ? item.players : [];
    players.forEach((player) => {
      if (!player?.id) {
        return;
      }

      if (!map[player.id]) {
        map[player.id] = [];
      }

      map[player.id].push(item);
    });
  });

  return map;
}

function createCourtBucket(items) {
  const map = {};

  items.forEach((item) => {
    const court = normalizeCourtId(item?.court);
    if (!court) {
      return;
    }

    if (!map[court]) {
      map[court] = [];
    }

    map[court].push(item);
  });

  return map;
}

function filterPlayers() {
  const query = normalizeForSearch(state.query);

  state.filteredPlayers = state.data.players.filter((player) => {
    if (!query) {
      return true;
    }

    const haystack = [
      player.name,
      player.country,
      player.tour,
      player.rankingTag,
      Number.isFinite(Number(player.ranking)) ? String(player.ranking) : "",
      Number.isFinite(Number(player.singlesRanking)) ? String(player.singlesRanking) : "",
      Number.isFinite(Number(player.doublesRanking)) ? String(player.doublesRanking) : ""
    ].join(" ");

    return normalizeForSearch(haystack).includes(query);
  });
}

function renderPlayerList() {
  if (!dom.playerList) {
    return;
  }

  if (!state.filteredPlayers.length) {
    dom.playerList.innerHTML = '<p class="card-sub">没有匹配到球员。</p>';
    return;
  }

  dom.playerList.innerHTML = "";

  state.filteredPlayers.forEach((player) => {
    const button = document.createElement("button");
    button.className = `player-item${player.id === state.activePlayerId ? " active" : ""}${player.overallEliminated ? " is-eliminated" : ""}`;
    button.type = "button";
    button.setAttribute("role", "listitem");

    const singlesLabel = player.singlesCount > 0
      ? `单${player.singlesOpenCount}/${player.singlesCount}`
      : "单0";
    const stats = [
      singlesLabel,
      player.doublesCount > 0 ? `双${player.doublesCount}` : "",
      `练${player.trainingCount}`
    ].filter(Boolean).join(" ");

    button.innerHTML = `
      <div class="player-main">
        <div class="player-list-topline">${renderPlayerListTopline(player)}</div>
        <div class="name">${escapeHtml(player.name)}</div>
        <div class="meta">${escapeHtml(stats)}</div>
      </div>
    `;

    button.addEventListener("click", () => {
      state.activePlayerId = player.id;
      storeActiveSelection("player", player.id);
      renderPlayerList();
      renderDetail();
    });

    dom.playerList.appendChild(button);
  });
}

function renderDetail() {
  const player = state.data?.playerById[state.activePlayerId];

  if (!player) {
    setHidden(dom.emptyState, false);
    setHidden(dom.playerDetail, true);
    return;
  }

  const singlesMatches = sortMatches(state.data.singlesByPlayer[player.id] || []);
  const doublesMatches = sortMatches(state.data.doublesByPlayer[player.id] || []);
  const trainingSessions = sortTraining(state.data.trainingByPlayer[player.id] || []);
  const allMatches = [...singlesMatches, ...doublesMatches];

  setHidden(dom.emptyState, true);
  setHidden(dom.playerDetail, false);

  const rankLabel = formatPlayerRankings(player);
  const tourBadgeHtml = player.tour ? renderTourBadge(player.tour) : '<span class="neutral-label">未识别</span>';
  setHtml(dom.playerTopline, `${tourBadgeHtml}<span class="topline-rank">${escapeHtml(rankLabel)}</span>${renderEntryTypeBadge(player.singlesEntryType)}${renderEliminationBadge(player)}`);
  setText(dom.playerName, player.name);
  setHtml(dom.playerIdentity, buildPlayerIdentityHtml(player));
  setText(dom.matchSplit, doublesMatches.length > 0
    ? `单 ${singlesMatches.length} / 双 ${doublesMatches.length}`
    : `单 ${singlesMatches.length}`);
  setText(dom.matchCount, `总计 ${allMatches.length} 场`);
  setText(dom.trainingCount, String(trainingSessions.length));
  setHidden(dom.doublesSection, doublesMatches.length === 0);

  renderMatchRows(dom.singlesMatchRows, player, singlesMatches, "singles");
  renderMatchRows(dom.doublesMatchRows, player, doublesMatches, "doubles");
  renderMatchRows(dom.matchRows, player, allMatches, "legacy");
  renderTrainingRows(player, trainingSessions);
}

function renderView() {
  const isPlayers = state.activeView !== "courts";

  storeActiveView(isPlayers ? "players" : "courts");

  setHidden(dom.playersView, !isPlayers);
  setHidden(dom.courtsView, isPlayers);

  if (dom.viewSwitch) {
    dom.viewSwitch.querySelectorAll("[data-view]").forEach((tab) => {
      const view = tab.getAttribute("data-view") || "";
      const active = view === (isPlayers ? "players" : "courts");
      tab.innerHTML = renderViewTabLabel(view);
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
  }

  renderSidebarState();
}

function renderSidebarState() {
  renderSingleSidebarState("players");
  renderSingleSidebarState("courts");
}

function renderSingleSidebarState(view) {
  const pane = dom[`${view}View`];
  const expand = dom[`${view}SidebarExpand`];
  const toggle = dom[`${view}SidebarToggle`];
  const collapsed = Boolean(state.sidebarCollapsed?.[view]);

  if (pane) {
    pane.classList.toggle("sidebar-collapsed", collapsed);
  }
  if (expand) {
    expand.hidden = !collapsed;
    expand.textContent = "展开";
  }
  if (toggle) {
    toggle.textContent = collapsed ? "展开" : "收起";
    toggle.setAttribute("aria-label", collapsed ? "展开侧栏" : "折叠侧栏");
  }
}

function setSidebarCollapsed(view, collapsed) {
  state.sidebarCollapsed[view] = collapsed;
  storeSidebarState(view, collapsed);
  renderSidebarState();
}

function renderCourtList() {
  if (!dom.courtList) {
    return;
  }

  if (!state.data?.courts?.length) {
    dom.courtList.innerHTML = '<p class="card-sub">暂无场地比赛数据。</p>';
    return;
  }

  dom.courtList.innerHTML = "";

  state.data.courts.forEach((court) => {
    const button = document.createElement("button");
    const meta = formatCourtListMeta(court);
    const statusPills = renderCourtStatusPills(court);
    const footer = [meta ? `<div class="meta court-list-meta">${escapeHtml(meta)}</div>` : "", statusPills]
      .filter(Boolean)
      .join("");
    button.className = `player-item${court.id === state.activeCourtId ? " active" : ""}`;
    button.type = "button";
    button.setAttribute("role", "listitem");
    button.setAttribute("data-court-id", court.id);

    button.innerHTML = `
      <div class="player-main">
        <div class="player-head">
          <div class="name">${escapeHtml(court.name)}</div>
        </div>
        ${footer ? `<div class="court-list-footer">${footer}</div>` : ""}
      </div>
    `;

    dom.courtList.appendChild(button);
  });
}

function renderCourtDetail() {
  const court = state.data?.courtById?.[state.activeCourtId];
  const matches = sortMatches(state.data?.matchesByCourt?.[state.activeCourtId] || []);
  const training = sortCourtTraining(state.data?.trainingByCourt?.[state.activeCourtId] || []);

  if (!court) {
    setHidden(dom.courtEmptyState, false);
    setHidden(dom.courtDetail, true);
    return;
  }

  setHidden(dom.courtEmptyState, true);
  setHidden(dom.courtDetail, false);
  setText(dom.courtName, formatCourtDisplayName(court.name));
  setText(dom.courtMeta, formatCourtMeta(court));
  setText(dom.courtMatchCount, String(court.matchCount + court.trainingCount));
  setText(dom.courtDayCount, `${court.dayCount} 天`);

  const grouped = groupCourtScheduleByDay(matches, training);
  dom.courtDaySections.innerHTML = grouped.length
    ? grouped.map((section) => renderCourtDaySection(section)).join("")
    : '<section class="table-card"><div class="table-wrap"><table><tbody><tr><td class="card-sub">暂无比赛或训练安排。</td></tr></tbody></table></div></section>';
}

function renderMatchRows(target, player, matches, discipline) {
  if (!target) {
    return;
  }

  if (!matches.length) {
    const emptyLabel = discipline === "doubles"
      ? "暂无双打比赛记录。"
      : discipline === "singles"
        ? "暂无单打比赛记录。"
        : "暂无比赛记录。";
    target.innerHTML = `<tr><td colspan="5" class="card-sub">${emptyLabel}</td></tr>`;
    return;
  }

  target.innerHTML = matches
    .map((match) => {
      const roundText = escapeHtml(formatMatchRound(match));
      const displayResult = renderMatchResultHtml(player, match);
      const displayTime = formatMatchTime(match);
      const matchDiscipline = getMatchDisplayDiscipline(match, discipline);
      const displayPair = buildOpponentSummaryHtml(player, match, matchDiscipline);
      const displayCourt = formatMatchCourt(match);

      return `
        <tr>
          <td>${escapeHtml(displayTime)}</td>
          <td>${roundText}</td>
          <td>${displayPair}</td>
          <td>${displayResult}</td>
          <td>${renderCourtLink(match, displayCourt)}</td>
        </tr>
      `;
    })
    .join("");
}

function formatMatchRound(match) {
  const roundLabel = String(match?.roundLabel || "").trim();
  if (roundLabel && roundLabel !== "-") {
    return compactRoundLabel(roundLabel);
  }

  const round = String(match?.roundCode || match?.round || "").trim() || "-";
  const draw = String(match?.draw || "").trim().toUpperCase();
  const normalizedRound = normalizeRoundLabel(draw, round);

  if (normalizedRound) {
    return normalizedRound;
  }

  if (draw === "QS" || draw === "QD") {
    return `资格赛 ${round}`;
  }

  if (draw === "MS" || draw === "MD") {
    return round;
  }

  return round;
}

function normalizeRoundLabel(draw, round) {
  const code = String(round || "").trim().toUpperCase();

  if (draw === "QS" || draw === "QD") {
    if (code === "Q1" || code === "R1") {
      return "资格赛第一轮";
    }
    if (code === "Q2" || code === "R2") {
      return "资格赛第二轮";
    }
    if (code === "Q3" || code === "R3") {
      return "资格赛第三轮";
    }
    return "";
  }

  if (draw === "MS" || draw === "MD") {
    if (code === "R128" || code === "R1") {
      return "第一轮";
    }
    if (code === "R64" || code === "R2" || code === "R6") {
      return "第二轮";
    }
    if (draw === "MD" && code === "R32") {
      return "第一轮";
    }
    if (code === "R32" || code === "R3") {
      return "第三轮";
    }
    if (code === "R16" || code === "R4") {
      return "16强";
    }
    if (code === "QF" || code === "R5") {
      return "8强";
    }
    if (code === "SF") {
      return "半决赛";
    }
    if (code === "F") {
      return "决赛";
    }
    return "";
  }

  return "";
}

function compactRoundLabel(label) {
  return String(label || "")
    .trim()
    .replace(/^正赛/, "");
}

function renderTrainingRows(player, sessions) {
  if (!dom.trainingRows) {
    return;
  }

  if (!sessions.length) {
    dom.trainingRows.innerHTML = `<tr><td colspan="4" class="card-sub">暂无训练安排。</td></tr>`;
    return;
  }

  dom.trainingRows.innerHTML = sessions
    .map((session) => {
      const partners = (session.players || []).filter((entry) => entry.id !== player.id);
      const partnersHtml = renderLinkedPlayers(partners);

      return `
        <tr>
          <td>${escapeHtml(session.dayLabel || "-")}</td>
          <td>${escapeHtml(formatTrainingTime(session))}</td>
          <td>${renderCourtLink(session, session.court || "-")}</td>
          <td>${partnersHtml || "单人或未公开"}</td>
        </tr>
      `;
    })
    .join("");
}

function renderCourtDaySection(section) {
  return `
    <section class="table-card">
      <div class="table-title">
        <h2>${escapeHtml(section.label)}</h2>
        <p>${escapeHtml(formatCourtDaySummary(section))}</p>
      </div>
      ${section.matches.length ? `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>时间 / 顺序</th>
              <th>赛事 / 轮次</th>
              <th>对阵信息</th>
              <th>比分 / 结果</th>
            </tr>
          </thead>
          <tbody>
            ${section.matches.map((match) => `
              <tr class="${isLiveMatchStatus(match.status) ? "match-row-live" : ""}">
                <td>${escapeHtml(formatCourtTimeSlot(match))}</td>
                <td>${[renderTourBadge(getMatchTour(match)), escapeHtml(formatMatchRound(match))].filter(Boolean).join(" ")}</td>
                <td>${buildCourtMatchupHtml(match)}</td>
                <td>${renderCourtResultHtml(match)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
      ` : ""}
      ${section.training.length ? `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>训练时间</th>
              <th>赛事 / 训练预约</th>
            </tr>
          </thead>
          <tbody>
            ${section.training.map((session) => `
              <tr>
                <td>${escapeHtml(formatTrainingTime(session))}</td>
                <td>${[renderTourBadge(getTrainingTour(session)), renderLinkedPlayers(session.players || []) || "-"].filter(Boolean).join(" ")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
      ` : ""}
    </section>
  `;
}

function renderViewTabLabel(view) {
  if (view !== "courts") {
    return "球员比赛 &amp; 训练";
  }

  const activity = state.data?.courtActivity;
  const parts = [];
  const liveMatchCourtCount = activity?.liveMatchCourtCount ?? 0;
  const currentTrainingCourtCount = activity?.currentTrainingCourtCount ?? 0;

  if (liveMatchCourtCount > 0) {
    parts.push(`<span class="view-tab-status-part">🔴${liveMatchCourtCount}赛</span>`);
  }
  if (currentTrainingCourtCount > 0) {
    parts.push(`<span class="view-tab-status-part">🎾${currentTrainingCourtCount}练</span>`);
  }
  if (!parts.length) {
    return "场地";
  }

  return `场地 <span class="view-tab-status">${parts.join('<span class="view-tab-divider">·</span>')}</span>`;
}

function renderCourtStatusPills(court) {
  const parts = [];

  if ((court?.liveCount ?? 0) > 0) {
    parts.push('<span class="court-status-pill court-live-pill" aria-label="有比赛进行中" title="有比赛进行中">LIVE</span>');
  }
  if ((court?.currentTrainingCount ?? 0) > 0) {
    parts.push('<span class="court-status-pill court-training-pill" aria-label="有训练进行中" title="有训练进行中">训练中</span>');
  }
  if (!parts.length) {
    return "";
  }

  return `<div class="court-status-pills">${parts.join("")}</div>`;
}

function buildCourtMatchupHtml(match) {
  const players = Array.isArray(match?.players) ? match.players : [];
  if (!players.length) {
    return "-";
  }

  const discipline = getMatchDisplayDiscipline(match);
  const sideA = players.filter((player) => String(player?.side || "").toUpperCase() === "A");
  const sideB = players.filter((player) => String(player?.side || "").toUpperCase() === "B");

  if (sideA.length || sideB.length) {
    const left = renderLinkedPlayers(sideA, discipline) || "待定";
    const right = renderLinkedPlayers(sideB, discipline) || "待定";
    return `${left} <span class="versus-sep">vs</span> ${right}`;
  }

  return renderLinkedPlayers(players, discipline);
}

function getMatchDisplayDiscipline(match, fallback = "") {
  const raw = String(match?.discipline || fallback || "").trim().toLowerCase();
  if (raw === "singles" || raw === "doubles") {
    return raw;
  }

  const draw = String(match?.draw || "").trim().toUpperCase();
  if (draw.endsWith("D")) {
    return "doubles";
  }
  if (draw.endsWith("S")) {
    return "singles";
  }

  return "";
}

function getMatchTour(match) {
  const players = Array.isArray(match?.players) ? match.players : [];
  const tours = new Set(
    players
      .map((player) => String(player?.tour || "").trim().toUpperCase())
      .filter(Boolean)
  );

  if (tours.has("WTA") && !tours.has("ATP")) {
    return "WTA";
  }
  if (tours.has("ATP") && !tours.has("WTA")) {
    return "ATP";
  }

  const draw = String(match?.draw || "").trim().toUpperCase();
  if (draw === "MS" || draw === "MD") {
    return "ATP";
  }
  if (draw === "QS" || draw === "QD") {
    return "WTA";
  }

  return "";
}

function getTrainingTour(session) {
  const players = Array.isArray(session?.players) ? session.players : [];
  const tours = new Set(
    players
      .map((player) => String(player?.tour || "").trim().toUpperCase())
      .filter(Boolean)
  );

  if (tours.has("WTA") && !tours.has("ATP")) {
    return "WTA";
  }
  if (tours.has("ATP") && !tours.has("WTA")) {
    return "ATP";
  }

  return "";
}

function renderCourtResultHtml(match) {
  const scoreText = escapeHtml(match?.score || match?.result || "-");
  const isLive = isLiveMatchStatus(match?.status);
  const side = isLive ? inferLeadingSideFromScoreLine(match) : inferWinnerSide(match);
  let resultHtml = scoreText;

  if (side === "A" || side === "B") {
    const label = isLive
      ? (side === "A" ? "左侧领先" : "右侧领先")
      : (side === "A" ? "左侧胜" : "右侧胜");
    resultHtml = `<span class="result-badge result-side">${escapeHtml(label)}</span>${scoreText}`;
  }

  return appendStatusToResult(resultHtml, match?.status);
}

function buildOpponentSummaryHtml(player, match, discipline) {
  const roster = Array.isArray(match.players) ? match.players : [];
  const current = roster.find((entry) => entry.id === player.id);
  const fallbackPlayers = roster.filter((entry) => entry.id !== player.id);
  const fallback = renderLinkedPlayers(fallbackPlayers, discipline);

  if (!current) {
    return fallback || (match.result ? "见结果描述" : "-");
  }

  const sameSide = roster.filter((entry) => entry.id !== player.id && entry.side && current.side && entry.side === current.side);
  const opponents = roster.filter((entry) => entry.id !== player.id && (!current.side || !entry.side || entry.side !== current.side));

  if (discipline === "doubles") {
    const chunks = [];

    if (sameSide.length) {
      chunks.push(`搭档：${renderLinkedPlayers(sameSide, discipline)}`);
    }

    if (opponents.length) {
      chunks.push(`对手：${renderLinkedPlayers(opponents, discipline)}`);
    }

    return chunks.join(" · ") || fallback || (match.result ? "见结果描述" : "-");
  }

  return renderLinkedPlayers(opponents, discipline) || fallback || (match.result ? "见结果描述" : "-");
}

function sortMatches(matches) {
  return [...matches].sort(compareMatchesForDisplay);
}

function compareMatchesForDisplay(a, b) {
  const priorityA = getMatchDisplayPriority(a);
  const priorityB = getMatchDisplayPriority(b);
  if (priorityA !== priorityB) {
    return priorityA - priorityB;
  }

  const direction = priorityA === 2 ? -1 : 1;
  const scheduleComparison = compareMatchSchedulePosition(a, b, direction);
  if (scheduleComparison !== 0) {
    return scheduleComparison;
  }

  return direction * String(a?.id || "").localeCompare(String(b?.id || ""));
}

function getMatchDisplayPriority(match) {
  if (isLiveMatchStatus(match?.status)) {
    return 0;
  }
  if (isFinishedMatch(match?.status)) {
    return 2;
  }
  if (isCanceledMatchStatus(match?.status)) {
    return 3;
  }
  return 1;
}

function compareMatchSchedulePosition(a, b, direction) {
  const dayComparison = compareNullableNumbers(getMatchDaySortStamp(a), getMatchDaySortStamp(b), direction);
  if (dayComparison !== 0) {
    return dayComparison;
  }

  const orderA = getScheduleOrder(a);
  const orderB = getScheduleOrder(b);
  if (orderA > 0 && orderB > 0 && orderA !== orderB) {
    return (orderA - orderB) * direction;
  }

  const minuteComparison = compareNullableNumbers(getMatchScheduleMinutes(a), getMatchScheduleMinutes(b), direction);
  if (minuteComparison !== 0) {
    return minuteComparison;
  }

  const orderComparison = compareNullableNumbers(orderA > 0 ? orderA : null, orderB > 0 ? orderB : null, direction);
  if (orderComparison !== 0) {
    return orderComparison;
  }

  return compareNullableNumbers(getComparableMatchSortStamp(a), getComparableMatchSortStamp(b), direction);
}

function compareNullableNumbers(left, right, direction) {
  const hasLeft = Number.isFinite(left);
  const hasRight = Number.isFinite(right);

  if (hasLeft && hasRight) {
    return left === right ? 0 : (left - right) * direction;
  }
  if (hasLeft) {
    return -1;
  }
  if (hasRight) {
    return 1;
  }
  return 0;
}

function getMatchDaySortStamp(match) {
  const stamp = getCourtDaySortStamp(getCourtDayKey(match));
  return stamp >= 0 ? stamp : null;
}

function getMatchScheduleMinutes(match) {
  const scheduleMinutes = parseClockMinutes(formatScheduleClock(match?.scheduleTime));
  if (scheduleMinutes !== null) {
    return scheduleMinutes;
  }

  const raw = String(match?.startTime || "").trim();
  if (!raw || isPlaceholderStartTime(raw) || isMidnightStartTime(raw)) {
    return null;
  }

  const parsed = Date.parse(raw);
  if (!Number.isFinite(parsed)) {
    return null;
  }

  return getMadridClockMinutes(new Date(parsed));
}

function parseClockMinutes(value) {
  const match = String(value || "").match(/^(\d{1,2}):(\d{2})/);
  if (!match) {
    return null;
  }

  const hour = Number(match[1]);
  const minute = Number(match[2]);
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) {
    return null;
  }

  return hour * 60 + minute;
}

function getComparableMatchSortStamp(match) {
  const stamp = getMatchSortStamp(match);
  return stamp > 0 ? stamp : null;
}

function getMatchSortStamp(match) {
  const raw = String(match?.startTime || "");
  if (raw && !isPlaceholderStartTime(raw)) {
    const parsed = Date.parse(raw);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  const dayStamp = getScheduleDayStamp(match?.scheduleDay);
  if (dayStamp !== null) {
    return dayStamp + getScheduleOrder(match) * 60_000;
  }

  return 0;
}

function getScheduleDayStamp(raw) {
  const day = String(raw || "").split("T")[0];
  if (!day) {
    return null;
  }

  const parsed = Date.parse(`${day}T00:00:00+02:00`);
  return Number.isFinite(parsed) ? parsed : null;
}

function getScheduleOrder(match) {
  const order = Number(match?.scheduleOrder);
  return Number.isFinite(order) && order > 0 ? order : 0;
}

function sortTraining(sessions) {
  return [...sessions].sort((a, b) => {
    const dayA = Number(a.dayOffset ?? 99);
    const dayB = Number(b.dayOffset ?? 99);
    if (dayA !== dayB) {
      return dayA - dayB;
    }
    const timeA = parseTrainingStartMinutes(a.timeRange);
    const timeB = parseTrainingStartMinutes(b.timeRange);
    if (timeA !== timeB) {
      return timeA - timeB;
    }
    return (a.timeRange || "").localeCompare(b.timeRange || "");
  });
}

function sortCourtTraining(sessions) {
  return [...sessions].sort((a, b) => {
    const stampA = getTrainingSortStamp(a);
    const stampB = getTrainingSortStamp(b);
    return stampB - stampA;
  });
}

function getTrainingSortStamp(session) {
  const dayStamp = getCourtDaySortStamp(getTrainingDayKey(session));
  return dayStamp + parseTrainingStartMinutes(session?.timeRange) * 60_000;
}

function parseTrainingStartMinutes(value) {
  return parseTrainingRangeMinutes(value)?.start ?? 0;
}

function renderTourBadge(tour) {
  const code = (tour || "").toUpperCase();

  if (!code) {
    return '<span class="tour-badge tour-unknown">未标记</span>';
  }

  return `<span class="tour-badge tour-${code.toLowerCase()}">${escapeHtml(code)}</span>`;
}

function renderEntryTypeBadge(entryType) {
  const code = normalizeEntryType(entryType);
  if (!code) {
    return "";
  }

  const label = entryTypeLabels[code] || code;
  return `<span class="entry-badge entry-${code.toLowerCase()}">${escapeHtml(label)}</span>`;
}

function renderStatusChip(status) {
  const code = (status || "").toUpperCase();
  if (code === "F") {
    return "";
  }

  const label = statusLabels[code] || code || "未知";

  if (!label) {
    return "";
  }

  const isLive = isLiveMatchStatus(code);
  const className = code === "F" ? "status-f" : isLive ? "status-live" : "status-other";
  const icon = isLive ? '<span class="status-live-icon" aria-hidden="true"></span>' : "";
  return `<span class="status-chip ${className}">${icon}${escapeHtml(label)}</span>`;
}

function renderMatchResultHtml(player, match) {
  const rawResult = match?.score || match?.result || "-";
  const outcome = getPlayerOutcome(player, match);
  const outcomeBadge = renderOutcomeBadge(outcome);
  const scoreText = escapeHtml(rawResult);
  const resultHtml = outcomeBadge ? `${outcomeBadge}${scoreText}` : scoreText;

  return appendStatusToResult(resultHtml, match?.status);
}

function appendStatusToResult(resultHtml, status) {
  const statusChip = renderStatusChip(status);
  if (!statusChip) {
    return resultHtml;
  }

  return `<div class="result-stack">${resultHtml}${statusChip}</div>`;
}

function renderOutcomeBadge(outcome, textOverride = "") {
  const label = textOverride || (outcome === "win" ? "胜" : outcome === "lose" ? "负" : "");
  if (outcome === "win") {
    return `<span class="result-badge result-win">${escapeHtml(label)}</span>`;
  }
  if (outcome === "lose") {
    return `<span class="result-badge result-lose">${escapeHtml(label)}</span>`;
  }
  return "";
}

function renderEliminationBadge(player) {
  const label = getPlayerEliminationLabel(player);
  if (!label) {
    return "";
  }

  const className = player?.overallEliminated ? "elimination-badge is-out" : "elimination-badge";
  return `<span class="${className}">${escapeHtml(label)}</span>`;
}

function getPlayerEliminationLabel(player) {
  const singles = Boolean(player?.singlesEliminated);
  const doubles = Boolean(player?.doublesEliminated);

  if (singles && doubles) {
    return "单/双淘汰";
  }
  if (singles) {
    return "单淘汰";
  }
  if (doubles) {
    return "双淘汰";
  }
  return "";
}

function isDisciplineEliminated(player, matches) {
  if (!Array.isArray(matches) || matches.length === 0) {
    return false;
  }

  if (matches.some((match) => !isFinishedMatch(match.status))) {
    return false;
  }

  return matches.some((match) => {
    return isEliminationRound(match) && getPlayerOutcome(player, match) === "lose";
  });
}

function getPlayerSinglesEntryType(player, singlesMatches) {
  const explicit = normalizeEntryType(
    player?.singlesEntryType ||
    player?.entryType ||
    player?.mainDrawEntryType
  );
  if (explicit) {
    return explicit;
  }

  if (!Array.isArray(singlesMatches) || !singlesMatches.some(isMainDrawMatch)) {
    return "";
  }

  const qualifyingMatches = singlesMatches.filter(isQualifyingMatch);
  if (!qualifyingMatches.length) {
    return "";
  }

  const hasQualifyingLoss = qualifyingMatches.some((match) => {
    return isFinishedMatch(match?.status) && getPlayerOutcome(player, match) === "lose";
  });

  if (hasQualifyingLoss) {
    return "LL";
  }

  return qualifyingMatches.every((match) => getPlayerOutcome(player, match) !== "lose") ? "Q" : "";
}

function normalizeEntryType(value) {
  const code = String(value || "").trim().toUpperCase();
  return code.replace(/[^A-Z]/g, "");
}

function isMainDrawMatch(match) {
  const draw = String(match?.draw || "").trim().toUpperCase();
  const label = String(match?.roundLabel || "").trim();

  return draw === "MS" || draw === "LS" || /^正?赛?第/.test(label) || [
    "第一轮",
    "第二轮",
    "第三轮",
    "16强",
    "8强",
    "半决赛",
    "决赛"
  ].includes(label);
}

function isQualifyingMatch(match) {
  const draw = String(match?.draw || "").trim().toUpperCase();
  const label = String(match?.roundLabel || "").trim();
  const code = String(match?.roundCode || match?.round || "").trim().toUpperCase();

  return draw === "QS" || draw === "RS" || label.startsWith("资格赛") || isQualifyingRoundCode(code);
}

function isQualifyingRoundCode(code) {
  return ["Q", "Q1", "Q2", "Q3"].includes(String(code || "").trim().toUpperCase());
}

function isEliminationRound(match) {
  const label = String(match?.roundLabel || "").trim();
  const code = String(match?.roundCode || match?.round || "").trim().toUpperCase();

  if ([
    "资格赛第一轮",
    "资格赛第二轮",
    "资格赛第三轮",
    "第一轮",
    "第二轮",
    "第三轮",
    "正赛第一轮",
    "正赛第二轮",
    "正赛第三轮",
    "16强",
    "8强",
    "半决赛",
    "决赛"
  ].includes(label)) {
    return true;
  }

  return [
    "Q1",
    "Q2",
    "Q3",
    "R1",
    "R2",
    "R3",
    "R4",
    "R5",
    "R6",
    "R16",
    "R32",
    "R64",
    "R128",
    "RQ",
    "QF",
    "SF",
    "F"
  ].includes(code);
}

function getPlayerOutcome(player, match) {
  if (!isFinishedMatch(match?.status)) {
    return null;
  }

  const winnerSide = inferWinnerSide(match);
  if (!winnerSide) {
    return null;
  }

  const roster = Array.isArray(match?.players) ? match.players : [];
  const current = roster.find((entry) => entry?.id === player?.id);
  const currentSide = String(current?.side || "").toUpperCase();

  if (!currentSide || (currentSide !== "A" && currentSide !== "B")) {
    return null;
  }

  return currentSide === winnerSide ? "win" : "lose";
}

function inferWinnerSide(match) {
  const explicit = String(match?.winnerSide || "").toUpperCase();
  if (explicit === "A" || explicit === "B") {
    return explicit;
  }

  const byResultText = inferWinnerSideFromResultText(match);
  if (byResultText) {
    return byResultText;
  }

  const byScoreLine = inferWinnerSideFromScoreLine(match);
  if (byScoreLine) {
    return byScoreLine;
  }

  if (String(match?.id || "").startsWith("ATP-")) {
    return "A";
  }

  return null;
}

function inferWinnerSideFromResultText(match) {
  const resultText = String(match?.result || "");
  const winnerLabel = extractWinnerLabel(resultText);
  if (!winnerLabel) {
    return null;
  }

  const winnerTokens = tokenizeName(winnerLabel);
  if (!winnerTokens.length) {
    return null;
  }

  const roster = Array.isArray(match?.players) ? match.players : [];
  const sideTokens = { A: [], B: [] };
  roster.forEach((entry) => {
    const side = String(entry?.side || "").toUpperCase();
    if (side !== "A" && side !== "B") {
      return;
    }

    sideTokens[side].push(...tokenizeName(entry?.name || ""));
  });

  const scoreA = countTokenOverlap(winnerTokens, sideTokens.A);
  const scoreB = countTokenOverlap(winnerTokens, sideTokens.B);

  if (scoreA === scoreB || (scoreA === 0 && scoreB === 0)) {
    return null;
  }

  return scoreA > scoreB ? "A" : "B";
}

function extractWinnerLabel(resultText) {
  const match = String(resultText || "").match(/\s+d\s+/i);
  if (!match || match.index === undefined) {
    return "";
  }

  return resultText.slice(0, match.index).trim();
}

function tokenizeName(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\[[^\]]*\]/g, " ")
    .replace(/[^a-zA-Z0-9]+/g, " ")
    .toLowerCase()
    .split(" ")
    .filter((token) => token.length > 1);
}

function countTokenOverlap(left, right) {
  if (!left.length || !right.length) {
    return 0;
  }

  const rightSet = new Set(right);
  let score = 0;
  left.forEach((token) => {
    if (rightSet.has(token)) {
      score += 1;
    }
  });
  return score;
}

function inferWinnerSideFromScoreLine(match) {
  const sets = extractScoreLineSets(match);
  if (!sets.length) {
    return null;
  }

  let setsA = 0;
  let setsB = 0;

  sets.forEach(([a, b]) => {
    if (a > b) {
      setsA += 1;
    } else if (b > a) {
      setsB += 1;
    }
  });

  if (setsA === 0 && setsB === 0) {
    return null;
  }
  if (setsA === setsB) {
    return null;
  }

  return setsA > setsB ? "A" : "B";
}

function inferLeadingSideFromScoreLine(match) {
  const sets = extractScoreLineSets(match);
  if (!sets.length) {
    return null;
  }

  let setsA = 0;
  let setsB = 0;
  let currentSet = null;

  sets.forEach(([a, b]) => {
    if (currentSet) {
      return;
    }

    if (!isCompletedSetScore(a, b)) {
      currentSet = [a, b];
      return;
    }

    if (a > b) {
      setsA += 1;
    } else if (b > a) {
      setsB += 1;
    }
  });

  if (setsA !== setsB) {
    return setsA > setsB ? "A" : "B";
  }

  if (!currentSet) {
    return null;
  }

  const [currentA, currentB] = currentSet;
  if (currentA === currentB) {
    return null;
  }

  return currentA > currentB ? "A" : "B";
}

function extractScoreLineSets(match) {
  const raw = String(match?.score || match?.result || "");
  if (!raw) {
    return [];
  }

  return raw
    .replace(/,/g, " ")
    .split(/\s+/)
    .map((token) => parseSetToken(token))
    .filter(Boolean);
}

function isCompletedSetScore(a, b) {
  const high = Math.max(a, b);
  const low = Math.min(a, b);
  const diff = high - low;

  if (high === 7 && (low === 5 || low === 6)) {
    return true;
  }

  return high >= 6 && diff >= 2;
}

function parseSetToken(token) {
  const clean = String(token || "").trim();
  if (!clean) {
    return null;
  }

  const hyphenMatch = clean.match(/^(\d+)-(\d+)/);
  if (hyphenMatch) {
    return [Number(hyphenMatch[1]), Number(hyphenMatch[2])];
  }

  const compactMatch = clean.match(/^(\d)(\d)/);
  if (compactMatch) {
    return [Number(compactMatch[1]), Number(compactMatch[2])];
  }

  return null;
}

function isFinishedMatch(status) {
  return String(status || "").toUpperCase() === "F";
}

function isCanceledMatchStatus(status) {
  return String(status || "").toUpperCase() === "C";
}

function isLiveMatchStatus(status) {
  const code = String(status || "").toUpperCase();
  return code === "O" || code === "L" || code === "P";
}

function compareRanking(a, b) {
  const rankA = getPlayerSinglesSortRanking(a);
  const rankB = getPlayerSinglesSortRanking(b);

  if (rankA !== null && rankB !== null) {
    return rankA - rankB;
  }

  if (rankA !== null) {
    return -1;
  }

  if (rankB !== null) {
    return 1;
  }

  return 0;
}

function getPlayerSinglesSortRanking(player) {
  const primaryTag = normalizeRankingTag(player?.rankingTag);
  return getEffectiveNumericRanking(player?.singlesRanking ?? (primaryTag === "D" ? null : player?.ranking));
}

function compareCourtName(left, right) {
  const rankLeft = parseCourtOrder(left);
  const rankRight = parseCourtOrder(right);

  if (rankLeft !== null && rankRight !== null && rankLeft !== rankRight) {
    return rankLeft - rankRight;
  }
  if (rankLeft !== null && rankRight === null) {
    return -1;
  }
  if (rankLeft === null && rankRight !== null) {
    return 1;
  }

  return String(left || "").localeCompare(String(right || ""), "en", { numeric: true });
}

function parseCourtOrder(value) {
  const match = String(value || "").match(/court\s*(\d+)/i);
  if (!match) {
    return null;
  }

  const num = Number(match[1]);
  return Number.isFinite(num) ? num : null;
}

function getNumericRanking(value) {
  const rank = Number(value);
  return Number.isFinite(rank) && rank > 0 ? rank : null;
}

function getEffectiveNumericRanking(value, rankingTag = "") {
  return getNumericRanking(value);
}

function normalizeRankingTag(value) {
  return String(value || "").trim().toUpperCase();
}

function formatRanking(value, rankingTag = "") {
  const rank = getEffectiveNumericRanking(value, rankingTag);
  const tag = normalizeRankingTag(rankingTag);

  if (rank === null) {
    return "未收录";
  }

  return tag ? `${tag} #${rank}` : `#${rank}`;
}

function formatPlayerRankings(player) {
  const parts = [];
  const primaryTag = normalizeRankingTag(player?.rankingTag);
  const singlesValue = player?.singlesRanking ?? (primaryTag === "D" ? null : player?.ranking);
  const singles = formatRanking(singlesValue, player?.singlesRankingTag || "");
  const doubles = formatRanking(player?.doublesRanking ?? (primaryTag === "D" ? player?.ranking : null), player?.doublesRankingTag || "D");

  if (singles !== "未收录") {
    parts.push(`单 ${singles}`);
  }
  if (doubles !== "未收录") {
    parts.push(`双 ${doubles.replace(/^D\s*/, "")}`);
  }

  return parts.length ? parts.join(" / ") : "未收录";
}

function formatPlayerRankingForDiscipline(player, discipline) {
  const normalizedDiscipline = String(discipline || "").trim().toLowerCase();
  const primaryTag = normalizeRankingTag(player?.rankingTag);
  let value = null;
  let tag = "";

  if (normalizedDiscipline === "singles") {
    value = player?.singlesRanking ?? (primaryTag === "D" ? null : player?.ranking);
    tag = player?.singlesRankingTag || "";
  } else if (normalizedDiscipline === "doubles") {
    value = player?.doublesRanking ?? (primaryTag === "D" ? player?.ranking : null);
    tag = player?.doublesRankingTag || (primaryTag === "D" ? "" : "");
  } else {
    return formatPlayerRankings(player);
  }

  const rank = formatRanking(value, tag);
  return rank === "未收录" ? "" : rank.replace(/^D\s*/, "");
}

function normalizeCountryCode(value) {
  const code = String(value || "").trim().toUpperCase();
  return code;
}

function formatCountryForList(value) {
  return normalizeCountryCode(value);
}

function formatCountryForDetail(value) {
  const code = normalizeCountryCode(value);
  if (!code) {
    return "";
  }

  const zh = countryZhNames[code];
  return zh ? `${code}（${zh}）` : code;
}

function buildPlayerIdentityHtml(player) {
  const countryLabel = formatCountryForDetail(player?.country);
  const officialLink = buildOfficialLinkHtml(player);
  const chunks = [];

  if (countryLabel) {
    chunks.push(`<span>${escapeHtml(countryLabel)}</span>`);
  }
  if (officialLink) {
    chunks.push(officialLink);
  }

  return chunks.join(" · ") || "-";
}

function buildOfficialLinkHtml(player) {
  const url = buildOfficialProfileUrl(player);
  if (!url) {
    return "";
  }

  const tour = String(player?.tour || "").trim().toUpperCase();
  const label = tour === "ATP" || tour === "WTA" ? `${tour} 官网` : "官方主页";
  return `<a class="official-link" href="${escapeHtml(url)}" target="_blank" rel="noreferrer noopener">${escapeHtml(label)}</a>`;
}

function buildOfficialProfileUrl(player) {
  const tour = String(player?.tour || "").trim().toUpperCase();
  const name = String(player?.name || "").trim();
  const nameQuery = encodeURIComponent(name);

  if (tour === "ATP") {
    const atpId = normalizeAtpPlayerId(player?.atpPlayerId);
    if (atpId) {
      return `https://www.atptour.com/en/players/-/${atpId.toLowerCase()}/overview`;
    }
    return nameQuery ? `https://www.atptour.com/en/search-results/all/${nameQuery}` : "";
  }

  if (tour === "WTA") {
    const wtaId = normalizeWtaPlayerId(player?.wtaPlayerId);
    if (wtaId) {
      const slug = slugifyPathSegment(name);
      return slug
        ? `https://www.wtatennis.com/players/${wtaId}/${slug}`
        : `https://www.wtatennis.com/players/${wtaId}`;
    }
    return nameQuery ? `https://www.wtatennis.com/search?query=${nameQuery}` : "";
  }

  return "";
}

function normalizeAtpPlayerId(value) {
  const id = String(value || "").trim().toUpperCase();
  return /^[A-Z0-9]{4}$/.test(id) ? id : "";
}

function normalizeWtaPlayerId(value) {
  const id = String(value || "").trim();
  return /^\d{3,10}$/.test(id) ? id : "";
}

function slugifyPathSegment(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function formatPlayerSuffix(player, discipline = "") {
  const parts = [];
  const countryLabel = formatCountryForList(player?.country);

  if (countryLabel) {
    parts.push(escapeHtml(countryLabel));
  }

  const rankingLabel = discipline
    ? formatPlayerRankingForDiscipline(player, discipline)
    : formatPlayerRankings(player);
  if (rankingLabel && rankingLabel !== "未收录") {
    parts.push(escapeHtml(rankingLabel));
  }

  return parts.length ? ` ${parts.join(" ")}` : "";
}

function renderLinkedPlayer(player, discipline = "") {
  const nameLabel = escapeHtml(player?.name || "未知球员");
  const suffix = formatPlayerSuffix(player, discipline);
  const playerId = String(player?.id || "").trim();

  if (playerId && state.data?.playerById?.[playerId]) {
    return `<a class="inline-player-link" href="#player-${escapeHtml(playerId)}" data-player-id="${escapeHtml(playerId)}">${nameLabel}</a>${suffix ? `<span class="inline-player-extra">${suffix}</span>` : ""}`;
  }

  return `<span class="inline-player-text">${nameLabel}${suffix ? `<span class="inline-player-extra">${suffix}</span>` : ""}</span>`;
}

function renderPlayerListRanking(player) {
  const ranking = formatPlayerRankingsForList(player);
  if (ranking === "未收录") {
    return "";
  }

  return `<div class="player-rank-note">${escapeHtml(ranking)}</div>`;
}

function renderPlayerListTopline(player) {
  const tour = String(player?.tour || "").trim().toUpperCase();
  const ranking = formatPlayerRankingsForList(player);
  const country = formatCountryForList(player?.country);
  const parts = [];

  if (tour) {
    const badgeLabel = ranking !== "未收录" ? `${tour} ${ranking}` : tour;
    parts.push(renderPlayerListTourBadge(tour, badgeLabel));
  } else if (ranking !== "未收录") {
    parts.push(`<span class="player-list-rank">${escapeHtml(ranking)}</span>`);
  }
  const entryBadge = renderEntryTypeBadge(player?.singlesEntryType);
  if (entryBadge) {
    parts.push(entryBadge);
  }
  if (country) {
    parts.push(`<span class="player-list-country">${escapeHtml(country)}</span>`);
  }

  return parts.join(" ") || '<span class="player-list-country">-</span>';
}

function formatPlayerRankingsForList(player) {
  const singlesCount = Number(player?.singlesCount || 0);
  const doublesCount = Number(player?.doublesCount || 0);
  const hasSingles = singlesCount > 0;
  const hasDoubles = doublesCount > 0;

  if (hasSingles && !hasDoubles) {
    return formatPlayerRankingForDiscipline(player, "singles") || "未收录";
  }

  if (hasDoubles && !hasSingles) {
    const doubles = formatPlayerRankingForDiscipline(player, "doubles");
    return doubles ? `双 ${doubles}` : "未收录";
  }

  return formatPlayerRankings(player);
}

function renderPlayerListTourBadge(tour, label) {
  const code = String(tour || "").toUpperCase();
  if (!code) {
    return "";
  }

  return `<span class="tour-badge tour-${code.toLowerCase()}">${escapeHtml(label)}</span>`;
}

function renderLinkedPlayers(players, discipline = "") {
  if (!Array.isArray(players) || players.length === 0) {
    return "";
  }

  return players.map((player) => renderLinkedPlayer(player, discipline)).join(" / ");
}

function renderCourtLink(item, fallbackLabel = "-") {
  const courtId = normalizeCourtId(item?.court);
  const label = escapeHtml(String(formatMatchCourt(item) || fallbackLabel || courtId || "-"));

  if (courtId && state.data?.courtById?.[courtId]) {
    return `<a class="inline-player-link" href="#court-${escapeHtml(courtId)}" data-court-id="${escapeHtml(courtId)}">${label}</a>`;
  }

  return `<span class="inline-player-text">${label}</span>`;
}

function normalizeForSearch(value) {
  return (value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function formatMatchTime(match, options = {}) {
  if (isLiveMatchStatus(match?.status)) {
    return LIVE_MATCH_TIME_LABEL;
  }

  const timeOnly = options.timeOnly === true;
  const raw = String(match?.startTime || "");
  const scheduleType = String(match?.scheduleType || "").toLowerCase();
  const shouldPreferSchedule = !isFinishedMatch(match?.status) && ["not_before", "followed_by", "after_rest"].includes(scheduleType);
  const scheduleLabel = formatScheduleLabel(match, { timeOnly });

  if (shouldPreferSchedule && scheduleLabel) {
    return scheduleLabel;
  }

  if (raw && !isPlaceholderStartTime(raw)) {
    if (isFinishedMatch(match?.status) || !isMidnightStartTime(raw)) {
      return timeOnly ? formatTime(raw) : formatDateTime(raw);
    }
  }

  if (scheduleLabel) {
    return scheduleLabel;
  }

  if (!raw || isPlaceholderStartTime(raw)) {
    return "待定";
  }

  return timeOnly ? formatTime(raw) : formatDateTime(raw);
}

function formatMatchCourt(match) {
  const court = normalizeCourtId(match?.court);
  const order = getScheduleOrder(match);
  const orderLabel = order > 0 ? `第${order}场` : "";

  if (court && orderLabel) {
    return `${court} · ${orderLabel}`;
  }
  return court || orderLabel || "-";
}

function normalizeCourtId(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return "";
  }

  const upper = raw.toUpperCase();
  if (courtAliases[upper]) {
    return courtAliases[upper];
  }

  const estadioMatch = upper.match(/^ESTADIO\s+(\d+)$/);
  if (estadioMatch) {
    return `Court ${Number(estadioMatch[1])}`;
  }

  const pistaMatch = upper.match(/^PISTA\s+(\d+)/);
  if (pistaMatch) {
    return `Court ${Number(pistaMatch[1])}`;
  }

  return raw;
}

function formatCourtMeta(court) {
  if (!court) {
    return "-";
  }

  const parts = [`${court.matchCount} 场比赛`];
  if (court.trainingCount > 0) {
    parts.push(`${court.trainingCount} 个训练`);
  }
  if (court.dayCount > 0) {
    parts.push(`${court.dayCount} 天`);
  }
  if (court.liveCount > 0) {
    parts.push(`${court.liveCount} 场进行中`);
  }
  return parts.join(" · ");
}

function formatCourtListMeta(court) {
  const parts = [];

  if ((court?.todayOpenCount ?? 0) > 0) {
    parts.push(`今 ${court.todayOpenCount}`);
  }
  if ((court?.openCount ?? 0) > 0) {
    parts.push(`全 ${court.openCount}`);
  }
  if ((court?.currentTrainingCount ?? 0) > 0) {
    parts.push(`练 ${court.currentTrainingCount}`);
  }

  return parts.join(" · ");
}

function formatCourtDisplayName(courtName) {
  const normalized = normalizeCourtId(courtName);
  if (normalized === "Court 1") {
    return "Court 1 - Estadio Manolo Santana";
  }
  if (normalized === "Court 2") {
    return "Court 2 - Estadio Arantxa Sanchez Vicario";
  }
  return normalized;
}

function groupCourtScheduleByDay(matches, training) {
  const groups = new Map();

  matches.forEach((match) => {
    const key = getCourtDayKey(match);
    if (!groups.has(key)) {
      groups.set(key, { matches: [], training: [] });
    }
    groups.get(key).matches.push(match);
  });

  training.forEach((session) => {
    const key = getTrainingDayKey(session);
    if (!groups.has(key)) {
      groups.set(key, { matches: [], training: [] });
    }
    groups.get(key).training.push(session);
  });

  return [...groups.entries()]
    .map(([key, entries]) => ({
      key,
      label: formatCourtDayLabel(key),
      stamp: getCourtDaySortStamp(key),
      hasOpenMatches: entries.matches.some(isOpenMatchForDisplay),
      matches: sortMatches(entries.matches),
      training: sortCourtTraining(entries.training)
    }))
    .sort(compareCourtDaySections);
}

function compareCourtDaySections(a, b) {
  const priorityA = getCourtDaySectionPriority(a);
  const priorityB = getCourtDaySectionPriority(b);
  if (priorityA !== priorityB) {
    return priorityA - priorityB;
  }

  if (priorityA === 1) {
    return a.stamp - b.stamp;
  }
  if (priorityA === 3) {
    return b.stamp - a.stamp;
  }

  if (a.stamp !== b.stamp) {
    return a.stamp - b.stamp;
  }
  return String(a.key || "").localeCompare(String(b.key || ""));
}

function getCourtDaySectionPriority(section) {
  const todayKey = getTodayCourtDayKey();
  const key = String(section?.key || "");

  if (key === todayKey && section?.hasOpenMatches) {
    return 0;
  }
  if (key !== "待定" && key > todayKey) {
    return 1;
  }
  if (key === todayKey) {
    return 2;
  }
  if (key !== "待定" && key < todayKey) {
    return 3;
  }
  return 4;
}

function isOpenMatchForDisplay(match) {
  return !isFinishedMatch(match?.status) && !isCanceledMatchStatus(match?.status);
}

function getCourtDayKey(match) {
  const scheduleDay = String(match?.scheduleDay || "").trim();
  if (scheduleDay) {
    return scheduleDay.slice(0, 10);
  }

  const startTime = String(match?.startTime || "").trim();
  if (startTime) {
    const matchDay = startTime.match(/^(\d{4}-\d{2}-\d{2})/);
    if (matchDay) {
      return matchDay[1];
    }
  }

  return "待定";
}

function getTrainingDayKey(session) {
  const raw = String(session?.dayLabel || "").trim();
  if (!raw) {
    return "待定";
  }

  const parsed = Date.parse(raw);
  if (!Number.isFinite(parsed)) {
    return "待定";
  }

  const date = new Date(parsed);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getCourtDaySortStamp(key) {
  if (key === "待定") {
    return -1;
  }

  const parsed = Date.parse(`${key}T00:00:00+02:00`);
  return Number.isFinite(parsed) ? parsed : -1;
}

function formatCourtDayLabel(key) {
  if (key === "待定") {
    return "待定";
  }

  return formatScheduleDay(key) || key;
}

function formatCourtDaySummary(section) {
  const parts = [];
  if (section.matches.length) {
    parts.push(`${section.matches.length} 场比赛`);
  }
  if (section.training.length) {
    parts.push(`${section.training.length} 个训练`);
  }
  return parts.join(" · ") || "-";
}

function formatTrainingTime(session) {
  return formatTrainingTimeRange(session?.timeRange);
}

function isCurrentTrainingSession(session) {
  const todayKey = getTodayCourtDayKey();
  const dayKey = getTrainingDayKey(session);

  if (dayKey !== todayKey) {
    return false;
  }

  const nowMinutes = getMadridNowMinutes();
  const range = parseTrainingRangeMinutes(session?.timeRange);
  if (!range) {
    return false;
  }

  return range.start <= nowMinutes && nowMinutes < range.end;
}

function parseTrainingRangeMinutes(value) {
  const raw = String(value || "");
  const match = raw.match(/(\d{1,2}):(\d{2})\s*(AM|PM)?\s*-\s*(\d{1,2}):(\d{2})\s*(AM|PM)/i);
  if (!match) {
    return null;
  }

  const startPeriod = match[3] || match[6];
  let start = parseMeridiemClockMinutes(match[1], match[2], startPeriod);
  let end = parseMeridiemClockMinutes(match[4], match[5], match[6]);
  if (start === null || end === null) {
    return null;
  }

  if (!match[3] && start > end) {
    start -= 12 * 60;
  }
  if (end <= start) {
    end += 24 * 60;
  }

  return { start, end };
}

function formatTrainingTimeRange(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return "-";
  }

  const range = parseTrainingRangeMinutes(raw);
  if (!range) {
    return raw;
  }

  return `${formatMinutesAsClock(range.start)} - ${formatMinutesAsClock(range.end)}`;
}

function formatMinutesAsClock(value) {
  const minutesInDay = 24 * 60;
  const normalized = ((value % minutesInDay) + minutesInDay) % minutesInDay;
  const hour = Math.floor(normalized / 60);
  const minute = normalized % 60;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function parseMeridiemClockMinutes(hourValue, minuteValue, periodValue) {
  const hourNumber = Number(hourValue);
  const minuteNumber = Number(minuteValue);
  const period = String(periodValue || "").toUpperCase();

  if (
    !Number.isFinite(hourNumber) ||
    !Number.isFinite(minuteNumber) ||
    hourNumber < 1 ||
    hourNumber > 12 ||
    minuteNumber < 0 ||
    minuteNumber > 59 ||
    (period !== "AM" && period !== "PM")
  ) {
    return null;
  }

  let hour = hourNumber % 12;
  if (period === "PM") {
    hour += 12;
  }

  return hour * 60 + minuteNumber;
}

function getMadridNowMinutes() {
  return getMadridClockMinutes(new Date());
}

function getMadridClockMinutes(date) {
  const formatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Madrid",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
  const parts = formatter.formatToParts(date);
  const hour = Number(parts.find((part) => part.type === "hour")?.value || "0");
  const minute = Number(parts.find((part) => part.type === "minute")?.value || "0");
  return hour * 60 + minute;
}

function getTodayCourtDayKey() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Madrid",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date());
}

function formatCourtTimeSlot(match) {
  if (isLiveMatchStatus(match?.status)) {
    const order = getScheduleOrder(match);
    return order > 0 ? `第${order}场 · ${LIVE_MATCH_TIME_LABEL}` : LIVE_MATCH_TIME_LABEL;
  }

  const timeLabel = formatMatchTime(match, { timeOnly: true });
  const order = getScheduleOrder(match);

  if (order > 0 && timeLabel && timeLabel !== "待定") {
    return `第${order}场 · ${timeLabel}`;
  }
  if (order > 0) {
    return `第${order}场`;
  }

  return timeLabel;
}

function openPlayer(playerId) {
  if (!playerId || !state.data?.playerById?.[playerId]) {
    return;
  }

  state.activePlayerId = playerId;
  storeActiveSelection("player", playerId);
  state.activeView = "players";
  renderPlayerList();
  renderDetail();
  renderView();
}

function openCourt(courtId) {
  if (!courtId || !state.data?.courtById?.[courtId]) {
    return;
  }

  state.activeCourtId = courtId;
  storeActiveSelection("court", courtId);
  state.activeView = "courts";
  renderCourtList();
  renderCourtDetail();
  renderView();
}

function getStoredView() {
  try {
    const value = window.localStorage.getItem(VIEW_STORAGE_KEY);
    return value === "courts" ? "courts" : "players";
  } catch {
    return "players";
  }
}

function storeActiveView(view) {
  try {
    window.localStorage.setItem(VIEW_STORAGE_KEY, view);
  } catch {
    // Ignore storage failures and fall back to in-memory state.
  }
}

function getStoredSelection(type) {
  try {
    return window.localStorage.getItem(SELECTION_STORAGE_KEYS[type]) || null;
  } catch {
    return null;
  }
}

function storeActiveSelection(type, id) {
  try {
    const key = SELECTION_STORAGE_KEYS[type];
    if (!key) {
      return;
    }
    if (id) {
      window.localStorage.setItem(key, id);
    } else {
      window.localStorage.removeItem(key);
    }
  } catch {
    // Ignore storage failures and fall back to in-memory state.
  }
}

function getStoredSidebarState(view) {
  try {
    return window.localStorage.getItem(SIDEBAR_STORAGE_KEYS[view]) === "1";
  } catch {
    return false;
  }
}

function storeSidebarState(view, collapsed) {
  try {
    window.localStorage.setItem(SIDEBAR_STORAGE_KEYS[view], collapsed ? "1" : "0");
  } catch {
    // Ignore storage failures and fall back to in-memory state.
  }
}

function formatScheduleLabel(match, options = {}) {
  const timeOnly = options.timeOnly === true;
  const scheduleType = String(match?.scheduleType || "").toLowerCase();
  const scheduleTime = formatScheduleClock(match?.scheduleTime);
  const dayLabel = formatScheduleDay(match?.scheduleDay);

  let core = "";
  if (scheduleType === "not_before") {
    core = scheduleTime ? `不早于 ${scheduleTime}` : "不早于";
  } else if (scheduleType === "starts_at") {
    core = scheduleTime ? `${scheduleTime} 开始` : "按排表开始";
  } else if (scheduleType === "followed_by") {
    core = "顺延";
  } else if (scheduleType === "after_rest") {
    core = "适当休息后";
  } else {
    core = localizeScheduleText(match?.scheduleDisplay || match?.scheduleText || "");
  }

  if (!core) {
    return "";
  }

  if (timeOnly) {
    return core;
  }

  return dayLabel ? `${dayLabel} ${core}` : core;
}

function formatScheduleDay(raw) {
  const match = String(raw || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) {
    return "";
  }
  return `${match[1]}/${Number(match[2])}/${Number(match[3])}`;
}

function formatScheduleClock(raw) {
  const match = String(raw || "").match(/^(\d{2}:\d{2})/);
  return match ? match[1] : "";
}

function localizeScheduleText(raw) {
  const normalized = normalizeForSearch(raw);
  if (!normalized) {
    return "";
  }
  if (normalized.includes("not before")) {
    return "不早于";
  }
  if (normalized.includes("starts at")) {
    return "按排表开始";
  }
  if (normalized.includes("followed by")) {
    return "顺延";
  }
  if (normalized.includes("after suitable rest")) {
    return "适当休息后";
  }
  return raw;
}

function isPlaceholderStartTime(raw) {
  return /T23:59(?::\d{2})?(?:[+-]\d{2}:?\d{2})?$/.test(String(raw || ""));
}

function isMidnightStartTime(raw) {
  return /T00:00(?::\d{2})?(?:[+-]\d{2}:?\d{2})?$/.test(String(raw || ""));
}

function formatDateTime(raw) {
  if (!raw) {
    return "待定";
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return raw;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Europe/Madrid"
  }).format(date);
}

function formatTime(raw) {
  if (!raw) {
    return "待定";
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return raw;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Europe/Madrid"
  }).format(date);
}

function setStatus(message) {
  setText(dom.refreshStatus, message);
}

function setText(node, value) {
  if (node) {
    node.textContent = value;
  }
}

function setHtml(node, value) {
  if (node) {
    node.innerHTML = value;
  }
}

function setHidden(node, hidden) {
  if (node) {
    node.hidden = hidden;
  }
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
