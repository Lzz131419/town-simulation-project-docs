<script setup lang="ts">
import { computed } from "vue";
import { itemNames, type Town } from "../../types";
const props = defineProps<{ world: Town }>();
const rows = computed(() =>
  Object.entries(props.world.market).map(([id, market]) => ({
    id,
    market,
    held: Object.values(props.world.agents).reduce(
      (n, a) => n + (a.inventory[id] ?? 0),
      0,
    ),
  })),
);
const max = computed(() =>
  Math.max(1, ...rows.value.map((r) => r.market + r.held)),
);
</script>
<template>
  <div class="resource-chart">
    <div class="chart-legend">
      <span><i></i>市场库存</span><span><i></i>居民持有</span>
    </div>
    <div v-for="row in rows" :key="row.id" class="resource-row">
      <div>
        <strong>{{ itemNames[row.id] }}</strong><span
          >{{ row.market }} / {{ row.held }}</span
        >
      </div>
      <div
        class="resource-track"
        role="img"
        :aria-label="`${itemNames[row.id]}，市场${row.market}份，居民持有${row.held}份`"
      >
        <i :style="{ width: (row.market / max) * 100 + '%' }"></i
        ><i :style="{ width: (row.held / max) * 100 + '%' }"></i>
      </div>
    </div>
  </div>
</template>
