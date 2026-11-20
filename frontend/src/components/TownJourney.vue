<script setup lang="ts">
import { computed } from "vue";
import {
  Navigation,
  Square,
  Play,
  ListOrdered,
  ChevronDown,
} from "lucide-vue-next";
import PlanQueue from "./PlanQueue.vue";
import { useTown } from "../stores/town";
import { pathDistance } from "../game/motion";
const { me, catalog, world, pending, connected, control } = useTown();
const destination = computed(() => {
  const task = me.value?.task;
  if (!task) return "";
  if (task.target_id)
    return world.value?.agents[task.target_id]?.name ?? "邻居";
  const id =
    task.type === "move" ? task.place : catalog.value.actions[task.type]?.place;
  return id ? (catalog.value.places[id]?.name ?? "目的地") : "当前位置";
});
const seconds = computed(() =>
  me.value
    ? Math.ceil(
        pathDistance(me.value, me.value.path) /
          (catalog.value.movement_per_tick ?? 40),
      ) * catalog.value.tick_seconds
    : 0,
);
const duration = computed(() =>
  seconds.value >= 60
    ? `${Math.floor(seconds.value / 60)}分${Math.ceil(seconds.value % 60)}秒`
    : `${Math.ceil(seconds.value)}秒`,
);
</script>
<template>
  <section v-if="me" class="town-journey" aria-label="我的当前行动">
    <div class="journey-main">
      <span class="journey-icon"><Navigation :size="17" /></span>
      <div class="journey-description">
        <strong>{{
          me.task
            ? destination
            : me.mode === "rules"
              ? "规则托管中"
              : me.mode === "plan"
                ? "按计划行动"
                : me.activity === "计划已暂停"
                  ? "计划已暂停"
                  : me.activity === "本轮计划已完成"
                    ? "本轮计划已完成"
                    : "等待新安排"
        }}</strong>
        <span v-if="me.task"
          >{{ catalog.actions[me.task.type]?.name ?? "前往" }} ·
          {{
            connected
              ? seconds > 0
                ? `约 ${duration}`
                : "即将抵达"
              : "等待同步"
          }}</span
        >
        <span v-else class="journey-outcome" :title="me.last_outcome">{{
          me.last_outcome || "选择一个地点开始行动"
        }}</span>
      </div>
      <button
        v-if="me.task || me.mode !== 'manual'"
        class="quiet compact"
        :disabled="pending || !connected"
        @click="control('manual')"
      >
        <Square :size="13" />{{ me.task ? "停止行动" : "接管角色" }}
      </button>
      <button
        v-else
        class="primary compact"
        :disabled="pending || !connected"
        @click="control(me.plan?.length ? 'plan' : 'rules')"
      >
        <Play :size="13" />{{ me.plan?.length ? "执行计划" : "启用规则托管" }}
      </button>
      <slot />
    </div>
    <details v-if="me.plan?.length" class="journey-plan">
      <summary>
        <ListOrdered :size="13" />待执行 {{ me.plan.length }} 项<span>{{
          me.mode === "manual"
            ? "已暂停"
            : me.mode === "plan"
              ? "完成即停"
              : "持续托管"
        }}</span
        ><ChevronDown :size="13" class="queue-chevron" />
      </summary>
      <PlanQueue />
    </details>
  </section>
</template>
