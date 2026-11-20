<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import type { Town, Catalog, TownEvent } from "../types";
import type { TownSceneHandle } from "../game/TownScene";
import MapMiniMap from "./MapMiniMap.vue";
import { layout, type CameraArea } from "../game/world-layout";

import {
  ZoomIn,
  ZoomOut,
  Maximize,
  LocateFixed,
  ScanEye,
  Layers,
  Map,
  ChevronRight,
  LoaderCircle,
} from "lucide-vue-next";
const props = defineProps<{
  world: Town;
  self: string;
  selected: string;
  catalog: Catalog;
  events: TownEvent[];
}>();
const emit = defineEmits<{
  select: [id: string];
  place: [id: string];
  expand: [];
}>();
const host = ref<HTMLDivElement>();
let game: import("phaser").Game | undefined;
let scene: TownSceneHandle | undefined;
let observer: ResizeObserver | undefined;
let disposed = false;
const ready = ref(false);
const names = ref(false);
const viewport = ref<CameraArea>();
const region = ref("town");
function focusRegion(id: string) {
  region.value = id;
  follow.value = false;
  if (id === "all") scene?.reset();
  else scene?.focusRegion(id);
}
const routes = ref(true),
  ambience = ref(true),
  follow = ref(false),
  layers = ref(false),
  guide = ref(false),
  mini = ref(true);
// Canvas backing resolution and art detail are independent of server coordinates.
onMounted(async () => {
  const Phaser = (await import("phaser")).default;
  const { makeTownScene } = await import("../game/TownScene");
  if (disposed || !host.value) return;
  const TownScene = makeTownScene(
    () => ({
      world: props.world,
      self: props.self,
      selected: props.selected,
      names: names.value,
      catalog: props.catalog,
      events: props.events,
      routes: routes.value,
      ambience: ambience.value,
      follow: follow.value,
    }),
    (event, value) => {
      if (event === "select") emit("select", value);
      else if (event === "freeCamera") {
        follow.value = false;
        region.value = "";
      } else emit("place", value);
    },
    (s) => (scene = s),
    (area) => {
      viewport.value = area;
      if (area.width > 0 && area.height > 0) ready.value = true;
    },
  );
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  game = new Phaser.Game({
    type: Phaser.CANVAS,
    parent: host.value!,
    backgroundColor: "#a4c88d",
    width: Math.round(host.value!.clientWidth * pixelRatio),
    height: Math.round(host.value!.clientHeight * pixelRatio),
    render: { antialias: true, pixelArt: false },
    scale: { mode: Phaser.Scale.NONE, zoom: 1 / pixelRatio },
    scene: TownScene,
    audio: { noAudio: true },
    banner: false,
  });
  observer = new ResizeObserver(() => {
    if (game && host.value)
      game.scale.resize(
        Math.round(host.value.clientWidth * pixelRatio),
        Math.round(host.value.clientHeight * pixelRatio),
      );
  });
  observer.observe(host.value!);
});
watch(
  () => props.world,
  () => scene?.sync(),
  { deep: false },
);
watch(
  () => props.selected,
  () => scene?.sync(),
);
watch([names, () => props.events], () => scene?.sync());
onBeforeUnmount(() => {
  disposed = true;
  observer?.disconnect();
  game?.destroy(true);
});
function previewPlace(x: number, y: number) {
  follow.value = false;
  region.value = "";
  scene?.focusAt(x, y);
}
function zoom(delta: number) {
  region.value = "";
  scene?.zoomBy(delta);
}
</script>
<template>
  <div class="game-map">
    <div class="map-topline">
      <span class="map-world-state"
        ><span class="status-dot"></span
        >{{
          (480 + world.tick * 10) % 1440 < 360 ||
          (480 + world.tick * 10) % 1440 >= 1140
            ? "夜晚"
            : (480 + world.tick * 10) % 1440 >= 1020
              ? "黄昏"
              : "白昼"
        }}<span
          >{{
            Object.values(world.agents).filter((a) => !a.npc && a.online).length
          }}
          位邻居在线</span
        ></span
      >
      <button
        class="map-guide-button"
        :aria-expanded="guide"
        @click="
          guide = !guide;
          layers = false;
        "
      >
        <Map :size="15" />地点导览
      </button>
    </div>
    <div class="map-regions" role="group" aria-label="地图分区">
      <button
        v-for="d in layout.districts"
        :key="d.id"
        :aria-pressed="region === d.id"
        @click="focusRegion(d.id)"
      >
        {{ d.name }}
      </button>
      <button :aria-pressed="region === 'all'" @click="focusRegion('all')">
        全镇
      </button>
    </div>
    <div v-if="guide" class="map-guide">
      <button
        v-for="(p, id) in catalog.places"
        :key="id"
        @mouseenter="previewPlace(p.x, p.y)"
        @focus="previewPlace(p.x, p.y)"
        @click="
          emit('place', String(id));
          guide = false;
        "
      >
        <span>{{ p.name }}</span><ChevronRight :size="14" />
      </button>
    </div>
    <div v-if="!ready" class="map-loading" role="status">
      <LoaderCircle :size="20" class="spin" />地图加载中
    </div>
    <div
      ref="host"
      class="phaser-host"
      :style="{ opacity: ready ? 1 : 0 }"
    ></div>
    <div class="map-controls">
      <button
        title="跟随所选居民"
        :aria-pressed="follow"
        :class="{ engaged: follow }"
        @click="follow = !follow"
      >
        <ScanEye :size="17" />
      </button>
      <button
        title="画面图层"
        :aria-expanded="layers"
        @click="
          layers = !layers;
          guide = false;
        "
      >
        <Layers :size="17" />
      </button>
      <button title="放大" @click="zoom(0.15)"><ZoomIn :size="17" /></button
      ><button title="缩小" @click="zoom(-0.15)"><ZoomOut :size="17" /></button
      ><button title="显示完整小镇" @click="focusRegion('all')">
        <LocateFixed :size="17" /></button
      ><button title="扩大地图" @click="emit('expand')">
        <Maximize :size="17" />
      </button>
    </div>
    <div v-if="layers" class="map-layer-menu">
      <label><input v-model="routes" type="checkbox" />行动路线</label>
      <label><input v-model="ambience" type="checkbox" />昼夜与环境动态</label>
      <label><input v-model="mini" type="checkbox" />小镇总览</label>
    </div>
    <MapMiniMap
      v-if="mini"
      :world="world"
      :selected="selected"
      :viewport="viewport"
      @locate="
        (x, y) => {
          follow = false;
          region = '';
          scene?.focusAt(x, y);
        }
      "
    />
    <label class="map-names"
      ><input v-model="names" type="checkbox" />居民姓名</label
    >
  </div>
</template>
