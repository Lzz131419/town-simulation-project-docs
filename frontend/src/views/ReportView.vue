<script setup lang="ts">
import { useTown } from "../stores/town";
import { actionNames, gameTime } from "../types";

import { ChevronRight, RefreshCw } from "lucide-vue-next";
import ReportDashboard from "../components/ReportDashboard.vue";
import EventDetails from "../components/EventDetails.vue";

const {
  user,
  world,
  me,
  report,
  history,
  eventActor,
  eventKind,
  loadEvents,
  who,
} = useTown();
</script>
<template>
  <template v-if="world && me && user"
    ><div v-if="report" class="report-metrics">
      <article class="card">
        <span>完成的行动</span><strong>{{ report.me.completed }}</strong>
      </article>
      <article class="card">
        <span>累计劳动与交易收入</span
        ><strong>{{ report.me.earned }}<small>镇币</small></strong>
      </article>
      <article class="card">
        <span>我的邻里联系</span
        ><strong
          >{{ Object.keys(report.me.relations).length
          }}<small>位</small></strong
        >
      </article>
      <article class="card">
        <span>共建贡献</span
        ><strong>{{ world.project.contributors[user.id] ?? 0 }}</strong>
      </article>
    </div>
    <ReportDashboard />
    <div class="two-col uneven">
      <article class="card">
        <div class="section-heading">
          <h2>小镇事件簿</h2>
          <button class="icon-button" title="刷新事件" @click="loadEvents()">
            <RefreshCw :size="16" />
          </button>
        </div>
        <div class="event-filters">
          <select v-model="eventActor" @change="loadEvents()">
            <option value="">全部居民</option>
            <option
              v-for="a in Object.values(world.agents)"
              :key="a.id"
              :value="a.id"
            >
              {{ a.name }}
            </option></select
          ><select v-model="eventKind" @change="loadEvents()">
            <option value="">全部类型</option>
            <option
              v-for="(label, id) in {
                ...actionNames,
                order: '订单',
                blocked: '行动受阻',
                plan: '计划',
                plan_done: '计划完成',
                plan_paused: '计划暂停',
                control: '控制',
                archive: '归档',
                construction: '建设',
                milestone: '成长徽章',
                levy: '维护金',
                fiscal: '国库结算',
              }"
              :key="id"
              :value="id"
            >
              {{ label }}
            </option>
          </select>
        </div>
        <details v-for="e in history" :key="e.id" class="event-line">
          <summary>
            <span class="event-dot"></span>
            <div>
              <strong>{{ e.text }}</strong><small
                >{{ gameTime(e.tick) }} · #{{ e.id }}</small
              >
            </div>
            <ChevronRight :size="14" />
          </summary>
          <EventDetails :details="e.details" />
        </details>
        <button
          v-if="history.length >= 50"
          class="quiet wide"
          @click="loadEvents(true)"
        >
          继续查看更早的记录
        </button>
      </article>
      <div class="stack-cards">
        <article class="card">
          <h2>伙伴们的生活足迹</h2>
          <div v-for="a in report?.ranking ?? []" :key="a.id" class="list-line">
            <strong>{{ a.name }}</strong><span>{{ a.completed }} 次行动</span
            ><span>{{ a.earned }} 镇币收入</span>
          </div>
        </article>
        <article class="card">
          <h2>我的邻里关系</h2>
          <div v-for="(n, id) in me.relations" :key="id" class="list-line">
            <span>{{ who(id) }}</span><strong>{{ n }} 亲近度</strong>
          </div>
          <p v-if="!Object.keys(me.relations).length" class="empty">
            暂无邻里关系
          </p>
        </article>
      </div>
    </div></template
  >
</template>
