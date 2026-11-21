<script setup lang="ts">
import { computed } from "vue";
import { invQty, itemNames, type Inventory } from "../types";

const props = defineProps<{ details?: Record<string, unknown> }>();
interface Assets {
  cash: number;
  energy: number;
  hunger: number;
  inventory: Inventory;
}
const changes = computed(() => {
  const before = props.details?.before as Assets | undefined;
  const after = props.details?.after as Assets | undefined;
  if (!before || !after) return [];
  return [
    { label: "镇币", from: before.cash, to: after.cash },
    { label: "精力", from: before.energy, to: after.energy },
    { label: "饥饿", from: before.hunger, to: after.hunger },
    ...Object.keys(before.inventory).map((key) => ({
      label: itemNames[key] ?? key,
      from: invQty(before.inventory[key]),
      to: invQty(after.inventory[key]),
    })),
  ].filter((change) => change.from !== change.to);
});
</script>

<template>
  <div class="event-details">
    <span v-for="change in changes" :key="change.label">
      {{ change.label }} <strong>{{ change.from }} → {{ change.to }}</strong>
    </span>
    <span v-if="details?.order_id"
      >订单 <strong>#{{ details.order_id }}</strong></span
    >
    <span v-if="details?.steps !== undefined"
      >计划 <strong>{{ details.steps }} 步</strong></span
    >
    <span v-if="!changes.length && !Object.keys(details ?? {}).length"
      >这条记录没有资产变化。</span
    >
  </div>
</template>
