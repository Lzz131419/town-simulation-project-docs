<script setup lang="ts">
import { ArrowUp, ArrowDown, X, Play, ArrowUpRight } from "lucide-vue-next";
import { useTown } from "../stores/town";
import { usePlanQueue } from "../composables/usePlanQueue";
const { me, pending, connected, control, go, actionText } = useTown();
const { edit } = usePlanQueue();
</script>
<template>
  <div v-if="me" class="plan-queue">
    <ol>
      <li v-for="(step, i) in me.plan" :key="i">
        <span class="queue-number">{{ String(i + 1).padStart(2, "0") }}</span>
        <strong>{{ actionText(step) }}</strong>
        <div class="queue-step-controls">
          <button
            :disabled="pending || !connected || i === 0"
            :aria-label="`上移第 ${i + 1} 步`"
            @click="edit(i, i - 1)"
          >
            <ArrowUp :size="13" />
          </button>
          <button
            :disabled="
              pending || !connected || i === (me.plan?.length ?? 0) - 1
            "
            :aria-label="`下移第 ${i + 1} 步`"
            @click="edit(i, i + 1)"
          >
            <ArrowDown :size="13" />
          </button>
          <button
            :disabled="pending || !connected"
            :aria-label="`移除第 ${i + 1} 步`"
            @click="edit(i)"
          >
            <X :size="13" />
          </button>
        </div>
      </li>
    </ol>
    <div class="queue-footer">
      <button
        v-if="me.mode !== 'plan'"
        class="primary compact"
        :disabled="pending || !connected || !me.plan?.length"
        @click="control('plan')"
      >
        <Play :size="13" />执行这份计划
      </button>
      <span v-else>执行完即停止</span>
      <button class="quiet compact" @click="go('agent')">
        更多安排<ArrowUpRight :size="13" />
      </button>
    </div>
  </div>
</template>
