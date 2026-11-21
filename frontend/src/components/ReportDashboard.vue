<script setup lang="ts">
import { computed, ref } from "vue";
import { useTown } from "../stores/town";
import TrendChart from "./charts/TrendChart.vue";
import ResourceChart from "./charts/ResourceChart.vue";
import RelationshipGraph from "./charts/RelationshipGraph.vue";
const { report, economy, world, me, loadReport } = useTown();
const metric = ref<
  "trade_amount" | "production" | "treasury" | "resident_cash" | "trades"
>("trade_amount");
const labels = {
  trade_amount: "每日交易额",
  production: "每日产量",
  treasury: "公共资金",
  resident_cash: "居民持有镇币",
  trades: "累计成交次数",
};
const points = computed(() =>
  ["trade_amount", "production"].includes(metric.value)
    ? (economy.value?.daily ?? []).map((s: any) => ({
        tick: s.day * 144,
        value:
          metric.value === "production"
            ? Object.values(s.production ?? {}).reduce(
                (sum: number, value: any) => sum + Number(value || 0),
                0,
              )
            : (s[metric.value] ?? 0),
      }))
    : (report.value?.series ?? []).map((s: any) => ({
        tick: s.tick,
        value: s[metric.value] ?? 0,
      })),
);
const latest = computed(() => report.value?.series?.at(-1) ?? world.value);
const weatherNames: Record<string, string> = {
  sunny: "晴天",
  cloudy: "多云",
  rain: "雨天",
  storm: "暴雨",
};
const seasonNames: Record<string, string> = {
  spring: "春季",
  summer: "夏季",
  autumn: "秋季",
  winter: "冬季",
};
</script>
<template>
  <section v-if="world && me" class="report-dashboard">
    <div class="report-overview">
      <article class="card report-chip">
        <span>当前国库</span
        ><strong>{{ latest?.treasury ?? world.treasury }}</strong
        ><small>镇币</small>
      </article>
      <article class="card report-chip">
        <span>居民总现金</span
        ><strong>{{ latest?.resident_cash ?? "—" }}</strong
        ><small>镇币</small>
      </article>
      <article class="card report-chip">
        <span>今日天气</span
        ><strong>{{
          weatherNames[latest?.weather ?? world.weather] ?? "—"
        }}</strong>
      </article>
      <article class="card report-chip">
        <span>当前季节</span
        ><strong>{{
          seasonNames[latest?.season ?? world.season] ?? "—"
        }}</strong>
      </article>
    </div>
    <article class="card economy-chart">
      <div class="section-heading">
        <h2>小镇经济走势</h2>
        <button class="quiet" @click="loadReport">刷新报表</button>
        <select v-model="metric" aria-label="趋势指标">
          <option v-for="(label, id) in labels" :key="id" :value="id">
            {{ label }}
          </option>
        </select>
      </div>
      <TrendChart
        :points="points"
        :label="labels[metric]"
        :unit="
          metric === 'production' ? '份' : metric === 'trades' ? '笔' : '镇币'
        "
      />
      <p class="fiscal-note" v-if="report?.fiscal">
        每日午夜，对超过
        {{ report.fiscal.protected_cash }}
        镇币或个人保留余额（取较高值）的部分收取
        {{ report.fiscal.daily_surplus_rate * 100 }}%
        公共维护金，向上取整，用于公共工作和市场收购。
      </p>
    </article>
    <article class="card">
      <h2>物资分布</h2>
      <ResourceChart :world="world" />
    </article>
    <article class="card">
      <h2>我的邻里关系网</h2>
      <RelationshipGraph :world="world" :me="me" />
    </article>
  </section>
</template>
