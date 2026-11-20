import { useReports } from "../composables/useReports";
import { useArchives } from "../composables/useArchives";
import { useMessages } from "../composables/useMessages";
import { useAgent } from "../composables/useAgent";

import { ref, computed, inject, type InjectionKey } from "vue";
import {
  Home,
  Users,
  Store,
  ClipboardList,
  Trees,
  MessagesSquare,
  BrainCircuit,
  Cloud,
  ChartNoAxesCombined,
} from "lucide-vue-next";
import { api, ApiError } from "../api";
import { applyPacket } from "../realtime/protocol";
import { createConnection } from "../realtime/connection";
import {
  members,
  itemNames,
  actionNames,
  placeNames,
  gameTime,
} from "../types";
import type {
  User,
  Town,
  Resident,
  TownEvent,
  Action,
  Catalog,
} from "../types";

export function createTownStore() {
  const catalog = ref<Catalog>({
    items: {},
    places: {},
    actions: {},
    members: [],
    tick_seconds: 2,
  });
  const returnSummary = ref<any>(null);
  const bootError = ref("");
  let generation = 0,
    disposed = false,
    initialized = false;
  const user = ref<User | null>(null),
    world = ref<Town | null>(null),
    events = ref<TownEvent[]>([]),
    revision = ref(-1),
    connected = ref(false),
    booting = ref(true);
  const view = ref("town"),
    selected = ref(""),
    focus = ref(false),
    toast = ref(""),
    error = ref(false),
    pending = ref(false),
    search = ref("");
  const loginForm = ref({ username: "wangjue", password: "" });
  const nav = [
    { id: "town", label: "小镇生活", icon: Home },
    { id: "residents", label: "邻里档案", icon: Users },
    { id: "market", label: "集市交易", icon: Store },
    { id: "orders", label: "合作订单", icon: ClipboardList },
    { id: "project", label: "共同建设", icon: Trees },
    { id: "messages", label: "邻里留言", icon: MessagesSquare },
    { id: "agent", label: "我的 AI 分身", icon: BrainCircuit },
    { id: "archives", label: "进度与归档", icon: Cloud },
    { id: "report", label: "生活记录", icon: ChartNoAxesCombined },
  ];
  const me = computed(() =>
    world.value && user.value ? world.value.agents[user.value.id] : null,
  );
  const person = computed(
    () => world.value?.agents[selected.value] ?? me.value,
  );
  const day = computed(() => gameTime(world.value?.tick ?? 0));
  const online = computed(
    () =>
      Object.values(world.value?.agents ?? {}).filter((a) => !a.npc && a.online)
        .length,
  );
  const roster = computed(() =>
    Object.values(world.value?.agents ?? {}).filter(
      (a) => a.name.includes(search.value) || a.id.includes(search.value),
    ),
  );
  const myPlan = computed(() => me.value?.plan ?? []);
  const bag = computed(() =>
    Object.values(me.value?.inventory ?? {}).reduce((a, b) => a + b, 0),
  );
  const colors = [
    "#575757",
    "#707070",
    "#8a8a8a",
    "#626262",
    "#969696",
    "#797979",
    "#505050",
    "#a0a0a0",
  ];
  let toastTimer: ReturnType<typeof setTimeout> | undefined;
  const connection = createConnection({
    message: (data) => apply(data),
    status: (value) => {
      connected.value = value;
    },
    expired: () => {
      resetSession();
      notify("登录已失效，请重新登录", true);
    },
  });
  const orderForm = ref({ item: "grain", quantity: 3, unit_price: 3 }),
    tradeQty = ref(1),
    contribute = ref({ item: "wood", quantity: 2 });
  const place = ref("");
  const page = computed(() => nav.find((n) => n.id === view.value));
  function notify(text: string, isError = false) {
    toast.value = text;
    error.value = isError;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toast.value = ""), 5000);
  }
  async function perform(fn: () => Promise<any>, success = "操作已完成") {
    if (pending.value) return;
    pending.value = true;
    const epoch = generation;
    try {
      await fn();
      if (success && epoch === generation) notify(success);
      if (epoch === generation) await refresh();
    } catch (e: any) {
      if (epoch === generation) notify(e.message, true);
    } finally {
      pending.value = false;
    }
  }
  function apply(data: unknown) {
    const next = applyPacket(
      world.value
        ? {
            type: "world",
            revision: revision.value,
            world: world.value,
            events: events.value,
          }
        : null,
      data,
    );
    if (next) {
      world.value = next.world;
      events.value = next.events;
      revision.value = next.revision;
    }
  }
  async function refresh() {
    const epoch = generation;
    if (user.value) {
      const data = await api("/world");
      if (epoch === generation && !disposed) apply(data);
    }
  }
  async function enter(u: User) {
    const epoch = ++generation;
    connection.stop();
    const [definitions, snapshot, summary] = await Promise.all([
      api<Catalog>("/catalog"),
      api("/world"),
      api("/return-summary"),
    ]);
    if (epoch !== generation || disposed) return;
    if (!snapshot?.world?.agents?.[u.id])
      throw Error("居民数据暂时不可用，请重试");
    revision.value = -1;
    world.value = null;
    apply(snapshot);
    catalog.value = definitions;
    user.value = u;
    selected.value = u.id;
    profile.value = { bio: u.bio, goal: u.goal };
    prompt.value = u.goal;
    messageForm.value.recipient_id = members.find((m) => m.id !== u.id)!.id;
    view.value = "town";
    policy.value = { ...me.value!.policy! };
    syncPlanDraft();
    returnSummary.value = summary?.completed ? summary : null;
    connection.start();
    try {
      await loadModel();
    } catch (e: any) {
      if (epoch === generation) notify(e.message, true);
    }
  }
  function resetSession() {
    generation++;
    connection.stop();
    resetAgent();
    resetReports();
    resetMessages();
    user.value = null;
    world.value = null;
    events.value = [];
    revision.value = -1;
    resetArchives();
    returnSummary.value = null;
    place.value = "";
    focus.value = false;
    selected.value = "";
    search.value = "";
    toast.value = "";
    orderForm.value = { item: "grain", quantity: 3, unit_price: 3 };
    contribute.value = { item: "wood", quantity: 2 };
    tradeQty.value = 1;
  }
  async function login() {
    if (pending.value) return;
    pending.value = true;
    try {
      await enter(await api("/auth/login", "POST", loginForm.value));
      loginForm.value.password = "";
      notify("欢迎回到雾河镇");
    } catch (e: any) {
      resetSession();
      notify(e.message, true);
    } finally {
      pending.value = false;
    }
  }
  async function logout() {
    try {
      await api("/auth/logout", "POST");
    } catch (e: any) {
      notify(e.message, true);
      return;
    }
    resetSession();
  }

  async function go(id: string) {
    const epoch = generation;
    view.value = id;
    place.value = "";
    try {
      if (id === "agent") {
        await loadModel();
        if (epoch !== generation || !me.value) return;
        policy.value = { ...me.value!.policy! };
        syncPlanDraft();
      }
      if (id === "messages") await refreshMessages();
      if (id === "archives") {
        const epoch = generation;
        const rows = await api("/archives");
        if (epoch === generation) archives.value = rows;
      }
      if (id === "report") {
        await Promise.all([loadReport(), loadEvents()]);
      }
    } catch (e: any) {
      notify(e.message, true);
    }
  }
  async function action(a: Action) {
    await perform(
      () => api("/me/action", "POST", a),
      "已接管角色并安排：" + actionNames[a.type],
    );
    place.value = "";
  }
  async function control(mode: string) {
    await perform(
      () => api("/me/control", "PUT", { mode }),
      mode === "rules"
        ? "计划与备用规则已启用"
        : mode === "plan"
          ? "开始执行计划，完成后停止"
          : "已接管，当前行动已停止",
    );
  }
  function selectResident(id: string) {
    selected.value = id;
  }
  function openPlace(id: string) {
    place.value = id;
  }
  function actionText(a: Action) {
    return `${actionNames[a.type] ?? a.type}${a.target_id ? " · " + who(a.target_id) : ""}${a.place ? " · " + placeNames[a.place] : ""}${a.item ? " · " + (a.quantity ?? 1) + " " + itemNames[a.item] : ""}`;
  }
  function who(id: string) {
    return world.value?.agents[id]?.name ?? id;
  }
  function initials(a: Resident) {
    return a.name.slice(-1);
  }
  function escape(e: KeyboardEvent) {
    if (e.key === "Escape") {
      focus.value = false;
      place.value = "";
      archiveDetail.value = null;
    }
  }
  async function initialize() {
    if (disposed) return;
    if (!initialized) {
      window.addEventListener("keydown", escape);
      initialized = true;
    }
    booting.value = true;
    bootError.value = "";
    try {
      await enter(await api("/me"));
    } catch (e: any) {
      resetSession();
      if (!(e instanceof ApiError && e.status === 401))
        bootError.value = e.message;
    } finally {
      booting.value = false;
    }
  }
  function dispose() {
    disposed = true;
    generation++;
    connection.stop();
    resetAgent();
    resetReports();
    resetMessages();
    resetArchives();
    clearTimeout(toastTimer);
    window.removeEventListener("keydown", escape);
  }

  const ctx = { user, world, me, myPlan, perform, refresh, notify };
  const {
    policy,
    profile,
    model,
    modelForm,
    prompt,
    aiBusy,
    aiResult,
    planDraft,
    planChoice,
    loadModel,
    saveModel,
    callAI,
    resetAgent,
    syncPlanDraft,
    savePlanDraft,
  } = useAgent(ctx);
  const { messages, messageForm, refreshMessages, sendMessage, resetMessages } =
    useMessages(ctx);
  const {
    archives,
    archiveTitle,
    archiveDetail,
    resetArchives,
    archive,
    showArchive,
    downloadArchive,
  } = useArchives(ctx);
  const {
    report,
    history,
    eventActor,
    eventKind,
    loadEvents,
    loadReport,
    resetReports,
  } = useReports(notify);
  return {
    catalog,
    returnSummary,
    user,
    world,
    events,
    revision,
    connected,
    booting,
    bootError,
    view,
    selected,
    focus,
    toast,
    error,
    pending,
    search,
    loginForm,
    nav,
    me,
    person,
    day,
    online,
    roster,
    myPlan,
    bag,
    colors,
    policy,
    profile,
    orderForm,
    tradeQty,
    contribute,
    messages,
    messageForm,
    model,
    modelForm,
    prompt,
    aiBusy,
    aiResult,
    archives,
    archiveTitle,
    archiveDetail,
    report,
    history,
    eventActor,
    eventKind,
    place,
    planDraft,
    planChoice,
    syncPlanDraft,
    savePlanDraft,
    page,
    notify,
    perform,
    refresh,
    login,
    logout,
    go,
    action,
    control,
    selectResident,
    openPlace,
    loadModel,
    saveModel,
    callAI,
    refreshMessages,
    sendMessage,
    archive,
    loadEvents,
    loadReport,
    showArchive,
    downloadArchive,
    actionText,
    who,
    initials,
    initialize,
    dispose,
  };
}
export type TownStore = ReturnType<typeof createTownStore>;
export const townKey: InjectionKey<TownStore> = Symbol("town");
export function useTown() {
  const store = inject(townKey);
  if (!store) throw Error("Town store is not provided");
  return store;
}
