<script setup lang="ts">
import { useTown } from "../../stores/town";

import { Coins, Package, Sun, ChevronRight } from "lucide-vue-next";

const { world, me, day, bag, page } = useTown();
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
          ><Package :size="17" />{{ bag }} /
          {{ world.project.completed ? 60 : 30 }}</span
        >
      </div>
    </header>
  </template>
</template>
