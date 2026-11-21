<script setup lang="ts">
import { computed, watch } from "vue";
import { useTown } from "../stores/town";
import { invQty, itemNames } from "../types";
import TrendChart from "../components/charts/TrendChart.vue";

import { Trees, ArrowRight, Package, Leaf } from "lucide-vue-next";

const productIcons: Record<string, string> = {
  vegetable: "菜",
  honey: "蜜",
  flax: "麻",
  cloth: "布",
  furniture: "椅",
  soup: "汤",
  grain: "✾",
  bread: "◒",
  wood: "▤",
  fruit: "●",
  fish: "⋈",
  ore: "⬡",
  herb: "❧",
  meal: "◉",
  tool: "⚒",
};
const {
  user,
  world,
  catalog,
  pending,
  me,
  bag,
  tradeQty,
  action,
  report,
  loadReport,
} = useTown();
type MarketRules = {
  rules?: {
    pricing?: {
      basic_items: string[];
      basic_target_stock: number;
      processed_target_stock: number;
    };
    simulation?: { sample_interval_ticks: number };
  };
};
type PriceSample = { tick: number; prices?: Record<string, number> };
const rules = computed(
  () => (catalog.value as typeof catalog.value & MarketRules).rules,
);
// Quotes mirror the server's pure function using live stock and published balance rules.
const quotes = computed(() => {
  const pricing = rules.value?.pricing;
  if (!pricing || !world.value) return {};
  return Object.fromEntries(
    Object.entries(world.value.market).map(([item, stock]) => {
      const base = catalog.value.items[item];
      if (!base) return [item, undefined];
      const target = pricing.basic_items.includes(item)
        ? pricing.basic_target_stock
        : pricing.processed_target_stock;
      const multiplier = Math.min(
        1.8,
        Math.max(0.5, 1 + 0.4 * Math.tanh((target - stock) / target)),
      );
      const roundedQuote = (value: number) =>
        Math.min(
          Math.floor(1.8 * value),
          Math.max(1, Math.ceil(0.5 * value), Math.round(value * multiplier)),
        );
      const buy = Math.max(
        Math.max(1, Math.ceil(0.5 * base.sell)) + 1,
        roundedQuote(base.buy),
      );
      const sell = Math.min(buy - 1, roundedQuote(base.sell));
      return [item, { buy, sell }];
    }),
  );
});
const trends = computed(() =>
  Object.fromEntries(
    Object.keys(world.value?.market ?? {}).map((item) => [
      item,
      ((report.value?.series ?? []) as PriceSample[])
        .filter((sample) => typeof sample.prices?.[item] === "number")
        .slice(-7)
        .map((sample) => ({ tick: sample.tick, value: sample.prices![item] })),
    ]),
  ),
);
watch(
  [
    () => user.value?.id,
    () =>
      Math.floor(
        (world.value?.tick ?? 0) /
          (rules.value?.simulation?.sample_interval_ticks ?? 6),
      ),
  ],
  () => {
    if (user.value && world.value) void loadReport();
  },
  { immediate: true },
);
</script>
<template>
  <template v-if="world && me && user">
    <div class="toolbar">
      <span
        >我的余额 <strong>{{ me.cash }}</strong> 镇币 · 背包 {{ bag }} 份</span
      ><label class="inline-label"
        >每次交易数量<input
          v-model.number="tradeQty"
          type="number"
          min="1"
          max="10"
      /></label>
    </div>
    <div class="three-col">
      <article
        v-for="(stock, id) in world.market"
        :key="id"
        class="card product-card"
      >
        <span class="product-art" :class="id">{{ productIcons[id] }}</span>
        <h2>{{ itemNames[id] }}</h2>
        <p class="muted">
          集市库存 {{ stock }} · 我持有 {{ invQty(me.inventory[id]) }}
        </p>
        <div class="price-row">
          <span
            >买入
            <strong>{{ quotes[id]?.buy ?? "—" }}</strong>
            镇币</span
          ><span
            >卖出
            <strong>{{ quotes[id]?.sell ?? "—" }}</strong>
            镇币</span
          >
        </div>
        <div class="price-trend">
          <span class="muted">买入价 · 最近7次采样</span>
          <TrendChart
            :points="trends[id] ?? []"
            :label="`${itemNames[id]}买入价趋势`"
            unit="镇币"
          />
        </div>
        <div class="button-row">
          <button
            class="primary"
            :disabled="pending"
            @click="action({ type: 'buy', item: id, quantity: tradeQty })"
          >
            购买</button
          ><button
            :disabled="pending"
            @click="action({ type: 'sell', item: id, quantity: tradeQty })"
          >
            出售
          </button>
          <button
            v-if="['bread', 'fruit', 'meal', 'soup'].includes(id)"
            :disabled="pending || !invQty(me.inventory[id])"
            @click="
              action({
                type:
                  id === 'soup'
                    ? 'eat_soup'
                    : id === 'fruit'
                      ? 'eat_fruit'
                      : id === 'meal'
                        ? 'eat_meal'
                        : 'eat',
              })
            "
          >
            食用
          </button>
        </div>
      </article>
    </div>
    <div class="section-heading"><h2>自己动手，也是一种经营</h2></div>
    <div class="three-col">
      <article class="card">
        <Leaf class="green-text" />
        <h3>晨光农场</h3>
        <p>收获3份谷物，消耗9精力。</p>
        <button class="quiet" @click="action({ type: 'farm' })">
          去收获<ArrowRight :size="15" />
        </button>
      </article>
      <article class="card">
        <Package class="ochre-text" />
        <h3>麦香面包房</h3>
        <p>2份谷物烘焙3份面包，消耗6精力。</p>
        <button class="quiet" @click="action({ type: 'bake' })">
          去烘焙<ArrowRight :size="15" />
        </button>
      </article>
      <article class="card">
        <Trees class="green-text" />
        <h3>木作工坊</h3>
        <p>制作2份木材，消耗10精力。</p>
        <button class="quiet" @click="action({ type: 'craft' })">
          去制作<ArrowRight :size="15" />
        </button>
      </article></div
  ></template>
</template>
<style scoped>
.price-trend {
  margin: 10px 0;
}
.price-trend > span {
  font-size: 11px;
}
.price-trend :deep(svg) {
  height: 90px;
}
.price-trend :deep(.chart-readout) {
  gap: 8px;
  margin: 4px 0;
}
.price-trend :deep(.chart-readout strong) {
  font-size: 14px;
}
.price-trend :deep(.chart-empty) {
  padding: 12px 0;
  margin: 0;
}
</style>
