<script setup lang="ts">
import { computed, ref } from "vue";
import { gameTime } from "../../types";
const props = defineProps<{
  points: { tick: number; value: number }[];
  label: string;
  unit?: string;
}>();
const active = ref<number | null>(null);
const ceiling = computed(
  () => Math.max(10, ...props.points.map((p) => p.value)) * 1.1,
);
const x = (i: number) =>
  44 +
  ((props.points[i].tick - props.points[0].tick) /
    Math.max(1, props.points.at(-1)!.tick - props.points[0].tick)) *
    510;
const y = (value: number) => 172 - (value / ceiling.value) * 135;
const path = computed(() =>
  props.points.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.value)}`).join(" "),
);
const shown = computed(
  () => props.points[active.value ?? props.points.length - 1],
);
</script>
<template>
  <div class="trend-chart">
    <div class="chart-readout">
      <strong
        >{{ shown?.value ?? "—" }} <small>{{ unit }}</small></strong
      ><span>{{ shown ? gameTime(shown.tick) : "等待采样" }}</span>
    </div>
    <p v-if="points.length < 2" class="chart-empty">
      {{
        points.length
          ? "已记录首个采样点，等待下一次采样"
          : "暂无历史数据，运行后自动记录"
      }}
    </p>
    <svg v-else viewBox="0 0 580 210" role="img" :aria-label="label">
      <g v-for="n in [0, 1, 2]" :key="n">
        <line
          x1="44"
          x2="554"
          :y1="37 + n * 67.5"
          :y2="37 + n * 67.5"
          stroke="#dddcd2"
          stroke-dasharray="3 5"
        />
        <text x="35" :y="41 + n * 67.5" text-anchor="end">
          {{ Math.round(ceiling * (1 - n / 2)) }}
        </text>
      </g>
      <path :d="path + ' L554,172 L44,172 Z'" fill="#e4edcb" opacity=".7" />
      <path
        :d="path"
        fill="none"
        stroke="#4b735b"
        stroke-width="2.5"
        stroke-linejoin="round"
      />
      <circle
        v-for="(p, i) in points"
        :key="p.tick"
        :cx="x(i)"
        :cy="y(p.value)"
        :r="active === i ? 5 : 3"
        :fill="active === i ? '#161616' : '#71916e'"
        tabindex="0"
        :aria-label="`${gameTime(p.tick)}，${p.value}${unit ?? ''}`"
        @mouseenter="active = i"
        @focus="active = i"
        @mouseleave="active = null"
        @blur="active = null"
      >
        <title>{{ gameTime(p.tick) }} · {{ p.value }}{{ unit }}</title>
      </circle>
      <text x="44" y="198">{{ gameTime(points[0].tick) }}</text>
      <text x="554" y="198" text-anchor="end">
        {{ gameTime(points.at(-1)!.tick) }}
      </text>
    </svg>
  </div>
</template>
