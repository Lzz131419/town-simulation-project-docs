<script setup lang="ts">
import { computed, ref } from "vue";
import { useTown } from "../stores/town";
import TrendChart from "./charts/TrendChart.vue";
import ResourceChart from "./charts/ResourceChart.vue";
import RelationshipGraph from "./charts/RelationshipGraph.vue";
const { report, world, me, loadReport } = useTown();
const metric = ref<"treasury" | "resident_cash" | "trades">("treasury");
const labels = {
  treasury: "公共资金",
  resident_cash: "居民持有镇币",
  trades: "累计成交次数",
};
const points = computed(() =>
  (report.value?.series ?? []).map((s: any) => ({
    tick: s.tick,
    value: s[metric.value],
  })),
);
</script>
<template>
  <section v-if="world && me" class="report-dashboard">
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
        :unit="metric === 'trades' ? '笔' : '镇币'"
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
