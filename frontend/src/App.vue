<script setup lang="ts">
import { provide, onMounted, onBeforeUnmount, computed } from "vue";
import { LoaderCircle, WifiOff, Check, X } from "lucide-vue-next";
import { createTownStore, townKey } from "./stores/town";
import LoginView from "./views/LoginView.vue";
import TownView from "./views/TownView.vue";
import ResidentsView from "./views/ResidentsView.vue";
import MarketView from "./views/MarketView.vue";
import OrdersView from "./views/OrdersView.vue";
import ProjectView from "./views/ProjectView.vue";
import MessagesView from "./views/MessagesView.vue";
import AgentView from "./views/AgentView.vue";
import ArchivesView from "./views/ArchivesView.vue";
import ReportView from "./views/ReportView.vue";
import ShellSidebar from "./components/layout/ShellSidebar.vue";
import ShellHeader from "./components/layout/ShellHeader.vue";
import ReturnDialog from "./components/dialogs/ReturnDialog.vue";
import PlaceDialog from "./components/dialogs/PlaceDialog.vue";
import ArchiveDialog from "./components/dialogs/ArchiveDialog.vue";
const store = createTownStore();
provide(townKey, store);
const {
  booting,
  user,
  world,
  me,
  view,
  focus,
  connected,
  page,
  toast,
  error,
  bootError,
} = store;
const views = {
  residents: ResidentsView,
  market: MarketView,
  orders: OrdersView,
  project: ProjectView,
  messages: MessagesView,
  agent: AgentView,
  archives: ArchivesView,
  report: ReportView,
};
const currentView = computed(() => views[view.value as keyof typeof views]);
onMounted(store.initialize);
onBeforeUnmount(store.dispose);
</script>
<template>
  <div v-if="booting" class="boot">
    <LoaderCircle class="spin" />正在连接雾河镇
  </div>
  <main v-else-if="bootError" class="connection-error" role="alert">
    <WifiOff :size="32" />
    <h1>暂时连接不上小镇</h1>
    <p>{{ bootError }}</p>
    <button class="primary" @click="store.initialize">重新连接</button>
  </main>
  <LoginView v-else-if="!user" />
  <div
    v-else-if="world && me"
    class="app-shell"
    :class="{ 'map-focus': focus }"
  >
    <ShellSidebar /><ShellHeader />
    <main class="main-area">
      <div v-if="!connected" class="connection-banner">
        <WifiOff :size="15" />连接暂时断开，角色将执行已有计划与规则。正在重连…
      </div>
      <TownView v-if="view === 'town'" />
      <section v-else class="workspace-page">
        <div class="page-heading">
          <h1>{{ page?.label }}</h1>
        </div>
        <component :is="currentView" />
      </section>
    </main>
    <ReturnDialog /><PlaceDialog /><ArchiveDialog />
  </div>
  <Transition name="toast"
    ><div v-if="toast" class="toast" :class="{ error }">
      <X v-if="error" :size="17" /><Check v-else :size="17" />{{ toast }}
    </div></Transition
  >
</template>
