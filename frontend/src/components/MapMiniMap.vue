<script setup lang="ts">
import type { Town } from "../types";
import { palette } from "../game/art/brush";
import { layout, type CameraArea } from "../game/world-layout";
const props = defineProps<{
  world: Town;
  selected: string;
  viewport?: CameraArea;
}>();
const emit = defineEmits<{ locate: [x: number, y: number] }>();
const { width, height } = layout.navigation;
function locate(event: PointerEvent) {
  const rect = (event.currentTarget as SVGSVGElement).getBoundingClientRect();
  emit(
    "locate",
    ((event.clientX - rect.left) / rect.width) * width,
    ((event.clientY - rect.top) / rect.height) * height,
  );
}
</script>
<template>
  <svg
    class="map-minimap"
    :viewBox="`0 0 ${width} ${height}`"
    role="button"
    tabindex="0"
    aria-label="小镇总览，点击定位"
    @pointerdown.stop="locate"
    @keydown.enter.prevent="
      emit(
        'locate',
        world.agents[selected]?.x ?? 512,
        world.agents[selected]?.y ?? 336,
      )
    "
  >
    <rect :width="width" :height="height" :fill="palette.grass" />
    <rect
      v-for="p in layout.parcels"
      :key="p.id"
      :x="p.x"
      :y="p.y"
      :width="p.w"
      :height="p.h"
      :fill="p.color"
      rx="6"
    />
    <rect
      :x="layout.river.x"
      y="0"
      :width="layout.river.width"
      :height="height"
      :fill="palette.water"
    />
    <rect
      v-for="(r, i) in layout.roads"
      :key="`r${i}`"
      :x="r.x"
      :y="r.y"
      :width="r.w"
      :height="r.h"
      :fill="palette.path"
    />
    <rect
      v-for="(b, i) in layout.bridges"
      :key="`bridge${i}`"
      :x="b.x"
      :y="b.y"
      :width="b.w"
      :height="b.h"
      fill="#bd9a65"
    />
    <rect
      v-for="b in layout.buildings"
      :key="b.id"
      :x="b.x"
      :y="b.y"
      :width="b.w"
      :height="b.h"
      rx="6"
      fill="#f5eed5"
      stroke="#617d68"
      stroke-width="5"
    />
    <rect x="388" y="342" width="231" height="118" rx="6" fill="#e5dfc6" />
    <path
      v-if="world.agents[selected]?.path.length"
      :d="
        `M${world.agents[selected].x},${world.agents[selected].y} ` +
        world.agents[selected].path.map((p) => `L${p.x},${p.y}`).join(' ')
      "
      fill="none"
      stroke="#fff9d1"
      stroke-width="7"
    />
    <circle
      v-for="a in props.world.agents"
      :key="a.id"
      :cx="a.x"
      :cy="a.y"
      :r="a.id === selected ? 15 : 9"
      :fill="a.id === selected ? '#fff1ae' : a.npc ? '#597e65' : '#3f6f88'"
      stroke="#fff8dc"
      stroke-width="4"
    />
    <rect
      v-if="viewport"
      class="minimap-viewport"
      :x="viewport.x"
      :y="viewport.y"
      :width="viewport.width"
      :height="viewport.height"
      fill="#fffce810"
      stroke="#fffef5"
      stroke-width="8"
    />
  </svg>
</template>
