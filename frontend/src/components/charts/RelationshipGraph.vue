<script setup lang="ts">
import { computed } from "vue";
import type { Town, Resident } from "../../types";
const props = defineProps<{ world: Town; me: Resident }>();
const nodes = computed(() =>
  Object.entries(props.me.relations)
    .filter(([id]) => props.world.agents[id])
    .map(([id, value], i, all) => ({
      id,
      value,
      name: props.world.agents[id].name,
      x: 220 + Math.cos((i / all.length) * Math.PI * 2 - Math.PI / 2) * 160,
      y: 140 + Math.sin((i / all.length) * Math.PI * 2 - Math.PI / 2) * 95,
    })),
);
</script>
<template>
  <p v-if="!nodes.length" class="chart-empty">
    与邻居交流后，这里会显示你们的联系
  </p>
  <svg
    v-else
    class="relationship-graph"
    viewBox="0 0 440 280"
    role="img"
    aria-label="我的邻里关系网"
  >
    <g v-for="n in nodes" :key="n.id">
      <line
        x1="220"
        y1="140"
        :x2="n.x"
        :y2="n.y"
        stroke="#a7bb92"
        :stroke-width="1 + n.value / 25"
      />
      <text :x="(220 + n.x) / 2 + 20" :y="(140 + n.y) / 2 + 4">
        {{ n.value }}
      </text>
      <circle :cx="n.x" :cy="n.y" r="20" fill="#fff" stroke="#333" />
      <text :x="n.x" :y="n.y + 5" class="node-initial">
        {{ n.name.slice(-1) }}
      </text>
      <text :x="n.x" :y="n.y + 35">{{ n.name }}</text>
    </g>
    <circle cx="220" cy="140" r="27" fill="#d5f267" stroke="#161616" />
    <text x="220" y="145" class="node-initial">{{ me.name.slice(-1) }}</text>
  </svg>
</template>
