<script setup lang="ts">
import { computed } from "vue";
import { Truck, Check, Coins } from "lucide-vue-next";
import { useTown } from "../stores/town";
import { usePlanQueue } from "../composables/usePlanQueue";
import { itemNames } from "../types";
const { world, me, catalog, action, pending } = useTown();
const { append } = usePlanQueue();
const today = computed(
  () => Math.floor(((world.value?.tick ?? 0) + 48) / 144) + 1,
);
const completed = computed(() =>
  me.value?.delivery_log?.day === today.value
    ? me.value.delivery_log.items
    : [],
);
const limit = computed(() => catalog.value.delivery_daily_limit ?? 3);
function shortage(inputs: Record<string, number>) {
  return Object.entries(inputs).some(
    ([k, n]) => (me.value?.inventory[k] ?? 0) < n,
  );
}
</script>
<template>
  <section class="delivery-board" aria-label="街区交付委托">
    <div class="delivery-summary">
      <span
        ><Truck :size="15" />今日交付 {{ completed.length }} / {{ limit }}</span
      ><span>全镇累计 {{ world?.supply?.completed ?? 0 }} 次</span>
    </div>
    <article
      v-for="(request, id) in catalog.deliveries"
      :key="id"
      class="delivery-request"
    >
      <div class="delivery-title">
        <h3>{{ request.name }}</h3>
        <strong><Coins :size="13" />{{ request.reward }} 镇币</strong>
      </div>
      <p v-for="(n, item) in request.inputs" :key="item">
        {{ itemNames[item] }}
        <span :class="{ missing: (me?.inventory[item] ?? 0) < n }"
          >{{ me?.inventory[item] ?? 0 }} / {{ n }}</span
        >
      </p>
      <div v-if="completed.includes(String(id))" class="delivery-done">
        <Check :size="14" />今日已交付
      </div>
      <p v-else-if="completed.length >= limit" class="delivery-note">
        今日额度已用完
      </p>
      <p
        v-else-if="(world?.treasury ?? 0) < request.reward"
        class="delivery-note"
      >
        公共预算不足
      </p>
      <div v-else class="delivery-buttons">
        <button
          class="primary compact"
          :disabled="pending || shortage(request.inputs)"
          @click="action({ type: 'delivery', item: String(id) })"
        >
          前往交付
        </button>
        <button
          class="compact"
          :disabled="pending || (me?.plan?.length ?? 0) >= 8"
          @click="append({ type: 'delivery', item: String(id) })"
        >
          加入计划
        </button>
      </div>
    </article>
    <p class="delivery-note">每项每日一次 · 到站交货后领取报酬</p>
  </section>
</template>
