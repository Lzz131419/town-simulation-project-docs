import { createSimulation, SCENARIO } from "../app/simulation.mjs";
import { renderProfile } from "./profile-view.mjs";
import {
  createTownMap,
  portrait,
  presentationFor,
  locations,
} from "./town-map.mjs";
const app = createSimulation(),
  $ = (id) => document.getElementById(id);
let selected = "resident-001",
  eventLimit = 50,
  historyMode = "behavior",
  agents = [],
  events = [],
  overview = null,
  feedbackTimer;
const labels = {
  WORLD_CREATED: "小镇迎来第一天",
  NEEDS_GREW: "日常需求增长",
  WORKED: "完成生产，领取工资",
  RESTED: "在住宅休息",
  WAGE_SHORTFALL: "公库暂不足以支付全额工资",
  FOOD_PURCHASED: "在集市购买粮食",
  FOOD_OUT_OF_STOCK: "集市粮食暂时售罄",
  INSUFFICIENT_PERSONAL_FUNDS: "购粮资金不足",
  WATER_CONSUMED: "在水井免费取水",
  WATER_OUT_OF_STOCK: "水井清水不足",
  SOCIAL_INTERACTION: "在广场与邻居交往",
  SOCIAL_SKIPPED: "今天没有形成社交配对",
  FACILITY_UNAVAILABLE: "广场暂不可用",
  DAY_SUMMARY: "小镇完成了一天的生活",
  DIGITAL_PROFILE_IMPORTED: "一位新邻居加入小镇",
  PROPOSAL_VOTED: "居民完成水井维修表决",
  PROPOSAL_EXECUTED: "老水井维修完成",
  FOOD_SHORTAGE: "小镇经历一次粮食短缺",
};
const fields = {
  food: "粮食",
  water: "清水",
  wood: "木材",
  treasury: "公库",
  cash: "余额",
  energy: "精力",
  hunger: "饥饿",
  waterNeed: "缺水需求",
  communityTrust: "社区信任",
  externalSpent: "对外支出",
  status: "议案状态",
  shortageApplied: "短缺已触发",
};
const statuses = {
    OPEN: "投票开放",
    APPROVED: "已通过 · 等待维修",
    REJECTED: "议案未通过",
    EXECUTED: "维修已完成",
  },
  jobNames = { farmer: "农夫", waterWorker: "取水工", resident: "普通居民" };
const entityName = (id) =>
  id === "town"
    ? "小镇"
    : id === "repair-well-01"
      ? "维修议案"
      : (agents.find((a) => a.agentId === id)?.displayName ??
        Object.values(locations).find((l) => l.facilityId === id)?.label ??
        id);
function el(tag, value = "", className) {
  const node = document.createElement(tag);
  node.textContent = String(value);
  if (className) node.className = className;
  return node;
}
function feedback(result, message) {
  clearTimeout(feedbackTimer);
  $("feedback").textContent = result.ok
    ? message
    : `${result.error.code} · ${result.error.message}`;
  $("feedback").className = result.ok ? "feedback" : "feedback error";
  if (result.ok)
    feedbackTimer = setTimeout(
      () => $("feedback").classList.add("quiet-feedback"),
      4200,
    );
  return result;
}
function send(type, payload = {}, message = "操作完成") {
  return feedback(
    app.dispatch({
      type,
      payload,
      expectedRevision: app.runtime.runtimeRevision,
    }),
    message,
  );
}
function options(select, items, emptyLabel) {
  const previous = select.value;
  select.replaceChildren();
  if (emptyLabel) select.add(new Option(emptyLabel, ""));
  for (const [id, name] of items) select.add(new Option(name, id));
  if (items.some(([id]) => id === previous)) select.value = previous;
}
function selectPanel(name) {
  for (const value of ["resident", "decision"]) {
    $(`tab-${value}`).setAttribute("aria-selected", String(value === name));
    $(`${value}-panel`).hidden = value !== name;
  }
}
function selectAgent(id) {
  selected = id;
  $("agent-select").value = id;
  selectPanel("resident");
  map.select(id);
  renderAgent();
  renderRoster();
}
const map = createTownMap($("town-map"), {
  onSelect: selectAgent,
  onLocation: (key) => {
    $("location-name").textContent = locations[key].label;
    $("location-description").textContent = locations[key].description;
    $("location-card").hidden = false;
  },
});
function displayValue(value) {
  if (typeof value === "boolean") return value ? "是" : "否";
  return statuses[value] ?? value;
}
function eventNode(event) {
  const li = el("li", labels[event.type] ?? "小镇事件");
  li.append(
    el(
      "span",
      `第${event.day}天 · 记录${event.sequence} · ${event.actorIds.map(entityName).join("、") || "小镇"}`,
      "event-meta",
    ),
  );
  const changes = event.effects
    .filter((d) => d.field !== "ballots")
    .map((d) => {
      let field = fields[d.field];
      if (!field && d.field.startsWith("relationships.")) {
        const [, id, key] = d.field.split(".");
        field = `与${entityName(id)}的${key === "trust" ? "信任" : "亲近度"}`;
      }
      return `${entityName(d.entityId)} ${field ?? d.field}：${displayValue(d.before)} → ${displayValue(d.after)}`;
    });
  if (changes.length)
    li.append(el("span", changes.join("；"), "event-effects"));
  return li;
}
function renderAgent() {
  const result = app.getAgent({ agentId: selected });
  if (!result.ok) return;
  const { agent, recentEvents } = result.data,
    index = agents.findIndex((a) => a.agentId === selected),
    root = $("agent-detail");
  root.replaceChildren();
  const top = el("div", "", "profile-top"),
    avatar = el("div", "", "portrait-frame"),
    canvas = el("canvas");
  canvas.width = 52;
  canvas.height = 62;
  portrait(canvas, index);
  avatar.append(canvas);
  const heading = el("div");
  heading.append(
    el("h2", agent.displayName),
    el(
      "p",
      agent.sourceType === "digitalPerson" ? "已授权数字居民" : "雾河镇居民",
    ),
    el("span", jobNames[agent.jobCode], "job-chip"),
  );
  top.append(avatar, heading);
  root.append(top);
  const activity = presentationFor(agent, events, overview.day),
    action = el("div", "", "current-action");
  action.append(el("span"), el("span", activity.action));
  root.append(action);
  for (const [name, key, color] of [
    ["精力", "energy", "#9bb76c"],
    ["饥饿", "hunger", "#c3a56e"],
    ["缺水", "waterNeed", "#85afb0"],
  ]) {
    const row = el("div", "", "need-row"),
      track = el("span", "", "need-track"),
      fill = el("i");
    fill.style.width = `${agent[key]}%`;
    fill.style.background = color;
    track.append(fill);
    row.append(el("span", name), track, el("span", agent[key], "need-value"));
    root.append(row);
  }
  const wallet = el("div", "", "personal-wallet");
  wallet.append(el("span", "个人余额"), el("strong", `${agent.cash} 镇币`));
  root.append(wallet);
  if (agent.sourceType === "digitalPerson") {
    const summary = el("div", "", "profile-summary");
    renderProfile(summary, agent);
    root.append(summary);
  }
  if (agent.hunger >= 80 || agent.waterNeed >= 80)
    root.append(
      el(
        "p",
        `${agent.hunger >= 80 ? "需要食物 " : ""}${agent.waterNeed >= 80 ? "需要清水" : ""}`,
        "warnings",
      ),
    );
  const history = $("agent-history");
  history.replaceChildren();
  if (historyMode === "relations") {
    for (const [id, rel] of Object.entries(agent.relationships)) {
      if (id === agent.agentId) continue;
      const row = el("div", "", "relation-row");
      row.append(
        el("span", entityName(id)),
        el("span", `信任 ${rel.trust} · 亲近 ${rel.affinity}`),
      );
      history.append(row);
    }
  } else if (!recentEvents.length)
    history.append(el("div", "暂无行为记录，推进一天看看吧。", "empty"));
  else
    for (const event of recentEvents) {
      const row = el("div", "", "history-item");
      row.append(
        el("strong", labels[event.type] ?? "小镇事件"),
        el("small", `第${event.day}天 · 记录${event.sequence}`),
      );
      history.append(row);
    }
}
function renderRoster() {
  const query = $("resident-search").value.trim().toLowerCase();
  $("roster-count").textContent = agents.length;
  const list = $("resident-roster");
  list.replaceChildren();
  agents.forEach((agent, index) => {
    if (
      query &&
      !`${agent.displayName} ${agent.agentId}`.toLowerCase().includes(query)
    )
      return;
    const button = el(
      "button",
      "",
      `resident-button${agent.agentId === selected ? " selected" : ""}`,
    );
    button.type = "button";
    button.setAttribute(
      "aria-label",
      `观察${agent.displayName}，${jobNames[agent.jobCode]}`,
    );
    button.setAttribute("aria-pressed", String(agent.agentId === selected));
    const canvas = el("canvas");
    canvas.width = 42;
    canvas.height = 51;
    portrait(canvas, index);
    button.append(canvas, el("span", agent.displayName));
    button.addEventListener("click", () => selectAgent(agent.agentId));
    list.append(button);
  });
  if (!list.children.length) list.append(el("div", "未找到居民", "empty"));
}
function renderTimeline() {
  const result = app.listEvents({
    agentId: $("event-agent").value,
    type: $("event-type").value,
  });
  if (!result.ok) return;
  const list = result.data.events;
  $("filtered-count").textContent = `共${list.length}条记录`;
  $("timeline").replaceChildren(...list.slice(0, eventLimit).map(eventNode));
  if (!list.length) $("timeline").append(el("li", "暂无行为记录", "empty"));
  $("more-events").hidden = list.length <= eventLimit;
}
function renderActivity() {
  const meaningful = events
    .filter((e) => !["NEEDS_GREW", "DAY_SUMMARY"].includes(e.type))
    .slice(0, 3);
  $("event-count").textContent = `共${events.length}条生活记录`;
  $("total-events").textContent = events.length;
  $("activity-feed").replaceChildren(
    ...meaningful.map((e) => {
      const card = el("div", "", "activity-card"),
        body = el("div");
      body.append(
        el(
          "strong",
          `${e.actorIds.length ? entityName(e.actorIds[0]) + " · " : ""}${labels[e.type]}`,
        ),
        el("small", `第${e.day}天 · 记录${e.sequence}`),
      );
      card.append(
        el(
          "span",
          e.type === "SOCIAL_INTERACTION"
            ? "···"
            : e.type === "WORKED"
              ? "✦"
              : "·",
          "activity-marker",
        ),
        body,
      );
      return card;
    }),
  );
}
function render() {
  const result = app.getOverview();
  if (!result.ok) return;
  overview = result.data;
  const s = overview,
    r = app.runtime;
  agents = app.listAgents().data.agents;
  events = app.listEvents().data.events;
  if (!agents.some((a) => a.agentId === selected)) selected = agents[0].agentId;
  $("runtime").textContent = r.busy
    ? "结算中"
    : r.paused
      ? "已暂停 · 可单步"
      : "生活正在继续";
  $("day").textContent = String(s.day).padStart(2, "0");
  for (const [id, val] of [
    ["population", s.agentCount],
    ["food", s.resources.food],
    ["water", s.resources.water],
    ["treasury", s.resources.treasury],
    ["trust", s.communityTrust],
  ])
    $(id).textContent = val;
  $("day-progress-fill").style.width = `${Math.min(100, (s.day / 30) * 100)}%`;
  $("day-progress-label").textContent =
    s.day >= 30 ? "30日观察已完成，可继续探索" : `30日观察计划 · ${s.day}/30`;
  const writable = r.paused && !r.busy;
  for (const id of [
    "create",
    "step",
    "export",
    "shortage",
    "vote",
    "execute",
    "profile-import",
  ])
    $(id).disabled = !writable;
  $("run").disabled = !writable;
  $("run").hidden = !r.paused;
  $("pause").hidden = r.paused;
  $("pause").disabled = r.busy;
  for (const id of ["profile-file", "snapshot-file"])
    $(id).disabled = !writable;
  $("shortage").disabled = !writable || s.shortageApplied;
  $("shortage").textContent = s.shortageApplied
    ? "✓ 已触发粮食短缺"
    : "◇ 触发粮食短缺";
  $("vote").disabled = !writable || s.proposal.status !== "OPEN";
  $("execute").disabled = !writable || s.proposal.status !== "APPROVED";
  $("profile-import").disabled =
    !writable || s.agentCount === 31 || s.proposal.status !== "OPEN";
  $("profile-file").disabled = $("profile-import").disabled;
  $("open-profile").disabled = $("profile-import").disabled;
  $("create").textContent = "重置";
  options(
    $("agent-select"),
    agents.map((a) => [a.agentId, a.displayName]),
  );
  $("agent-select").value = selected;
  options(
    $("event-agent"),
    agents.map((a) => [a.agentId, a.displayName]),
    "全部居民",
  );
  options($("event-type"), Object.entries(labels), "全部类型");
  renderAgent();
  renderRoster();
  renderActivity();
  if ($("events-dialog").open) renderTimeline();
  map.update(agents, events, s.day, selected, r.paused);
  $("proposal-status").textContent = statuses[s.proposal.status];
  const ballots = app.getBallots().data.ballots;
  const support = ballots.filter((b) => b.support).length;
  $("vote-result").textContent =
    s.proposal.status === "OPEN"
      ? "当前立场为预览，关闭投票后冻结。"
      : `支持${support}票 · 反对${ballots.length - support}票${s.proposal.status === "EXECUTED" ? ` · 已支出${s.externalSpent}镇币` : ""}`;
  $("ballots").replaceChildren(
    ...ballots.map((b) =>
      el(
        "div",
        `${entityName(b.agentId)} · ${b.support ? "支持" : "反对"} · 评分${b.score10 / 10}\n缺水${b.waterNeed} / 信任${b.communityTrust} / 亲近${b.affinity}`,
        "ballot",
      ),
    ),
  );
}
function openEvents() {
  renderTimeline();
  $("events-dialog").showModal();
}
$("create").addEventListener("click", () => {
  if (
    app.world &&
    !confirm(
      "重新创建小镇会清除当前内存进度与数字人物。已下载的存档不会被删除。继续？",
    )
  )
    return;
  send(
    "CREATE_WORLD",
    { config: SCENARIO },
    "小镇重新开始了：第0天，30名居民。",
  );
});
$("step").addEventListener("click", () =>
  send("STEP", {}, "居民们又度过了一天。"),
);
$("run").addEventListener("click", () =>
  feedback(app.resume(), "开始观察：每秒推进一天，可随时暂停。"),
);
$("pause").addEventListener("click", () =>
  feedback(app.pause(), "已暂停，点击居民看看今天发生了什么。"),
);
$("shortage").addEventListener("click", () => {
  const r = send("TRIGGER_SHORTAGE");
  if (r.ok)
    feedback(
      r,
      `粮食短缺：库存从${r.data.foodBefore}变为${r.data.foodAfter}。`,
    );
});
$("vote").addEventListener("click", () => {
  const r = send("CLOSE_VOTE", { proposalId: "repair-well-01" });
  if (r.ok)
    feedback(
      r,
      `表决完成：支持${r.data.support}票，反对${r.data.oppose}票。${statuses[r.data.status]}。`,
    );
});
$("execute").addEventListener("click", () =>
  send(
    "EXECUTE_PROPOSAL",
    { proposalId: "repair-well-01", proposalVersion: 1 },
    "老水井修好了：花费120镇币，清水增加30份，社区信任提升。",
  ),
);
$("open-profile").addEventListener("click", () =>
  $("profile-dialog").showModal(),
);
$("close-profile").addEventListener("click", () => $("profile-dialog").close());
$("profile-import").addEventListener("click", () => {
  const r = send(
    "IMPORT_PROFILE",
    { utf8Bytes: new TextEncoder().encode($("profile-text").value) },
    "新邻居加入了！在地图或居民列表中可以找到这位数字人物。",
  );
  if (r.ok) {
    $("profile-dialog").close();
    selectAgent("digital-001");
  }
});
async function importFile(input, type, limit) {
  const file = input.files[0];
  if (!file) return;
  try {
    const bytes =
      file.size > limit
        ? new Uint8Array(limit + 1)
        : new Uint8Array(await file.arrayBuffer());
    const r = send(
      type,
      { utf8Bytes: bytes },
      type === "IMPORT_SNAPSHOT"
        ? "存档已恢复，可以从这一天继续。"
        : "新邻居加入了小镇。",
    );
    if (r.ok && type === "IMPORT_PROFILE") {
      $("profile-dialog").close();
      selectAgent("digital-001");
    }
  } catch {
    $("feedback").textContent = "FILE_READ_FAILED · 文件读取失败，请重新选择。";
    $("feedback").className = "feedback error";
  } finally {
    input.value = "";
  }
}
$("profile-file").addEventListener("change", () =>
  importFile($("profile-file"), "IMPORT_PROFILE", 16384),
);
$("snapshot-file").addEventListener("change", () =>
  importFile($("snapshot-file"), "IMPORT_SNAPSHOT", 5242880),
);
$("export").addEventListener("click", () => {
  const result = app.exportSnapshot();
  if (!result.ok) return feedback(result, "");
  const url = URL.createObjectURL(
      new Blob([result.data.json], { type: "application/json" }),
    ),
    link = document.createElement("a");
  link.href = url;
  link.download = result.data.filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  feedback(result, "进度已保存为本地文件，之后可读取存档继续。");
});
$("agent-select").addEventListener("change", () =>
  selectAgent($("agent-select").value),
);
$("resident-search").addEventListener("input", renderRoster);
$("tab-resident").addEventListener("click", () => selectPanel("resident"));
$("tab-decision").addEventListener("click", () => selectPanel("decision"));
for (const [id, mode] of [
  ["show-behavior", "behavior"],
  ["show-relations", "relations"],
])
  $(id).addEventListener("click", () => {
    historyMode = mode;
    $("show-behavior").classList.toggle("active", mode === "behavior");
    $("show-relations").classList.toggle("active", mode === "relations");
    renderAgent();
  });
$("nav-town").addEventListener("click", () => {
  map.reset();
  selectPanel("resident");
});
$("nav-residents").addEventListener("click", () => {
  selectPanel("resident");
  $("resident-search").focus();
});
$("nav-events").addEventListener("click", openEvents);
$("all-events").addEventListener("click", openEvents);
$("close-events").addEventListener("click", () => $("events-dialog").close());
for (const id of ["event-agent", "event-type"])
  $(id).addEventListener("change", () => {
    eventLimit = 50;
    renderTimeline();
  });
$("more-events").addEventListener("click", () => {
  eventLimit += 50;
  renderTimeline();
});
$("zoom-in").addEventListener("click", () => map.zoom(0.2));
$("zoom-out").addEventListener("click", () => map.zoom(-0.2));
$("fit-map").addEventListener("click", () => map.reset());
$("show-names").addEventListener("change", () =>
  map.names($("show-names").checked),
);
$("show-actions").addEventListener("change", () =>
  map.actions($("show-actions").checked),
);
$("close-location").addEventListener(
  "click",
  () => ($("location-card").hidden = true),
);
app.subscribe(render);
send(
  "CREATE_WORLD",
  { config: SCENARIO },
  "雾河镇准备好了，点击“开始模拟”或“推进一天”看看吧。",
);
