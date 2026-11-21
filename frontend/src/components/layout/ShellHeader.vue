<script setup lang="ts">
import { computed } from "vue";
import { useTown } from "../../stores/town";

import { Coins, Package, Sun, ChevronRight } from "lucide-vue-next";

const { world, me, day, bag, page, catalog } = useTown();
const capacity = computed(() => {
  const home = world.value?.homes?.find(
    (h) => h.id === me.value?.home_id && h.owner_id === me.value?.id,
  );
  return (
    (world.value?.project.completed ? 60 : 30) +
    (home?.level ?? 0) * (catalog.value.rules?.homes?.capacity_per_level ?? 10)
  );
});
</script>
<template>
  <template v-if="world && me">
    <header class="topbar">
      <div class="breadcrumb">
        雾河镇 <ChevronRight :size="14" /><strong>{{ page?.label }}</strong>
      </div>
      <div class="topbar-right">
        <span class="clock"><Sun :size="17" />{{ day }}</span
        ><span class="top-metric"
          ><Coins :size="17" /><strong>{{ me.cash }}</strong> 镇币</span
        ><span class="top-metric"
          ><Package :size="17" />{{ bag }} / {{ capacity }}</span
        >
      </div>
    </header>
  </template>
</template>
