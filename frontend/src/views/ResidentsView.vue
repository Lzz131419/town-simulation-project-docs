<script setup lang="ts">
import { useTown } from "../stores/town";

import { ArrowUpRight } from "lucide-vue-next";

const { user, world, selected, search, me, roster, colors, go, initials } =
  useTown();
</script>
<template>
  <template v-if="world && me && user"
    ><div class="toolbar">
      <span>{{ roster.length }} 位居民</span>
      <input
        v-model="search"
        placeholder="查找姓名或用户名"
        aria-label="查找居民"
      />
    </div>
    <div class="resident-cards">
      <button
        v-for="(a, i) in roster"
        :key="a.id"
        class="card resident-card"
        @click="
          selected = a.id;
          go('town');
        "
      >
        <span class="avatar large" :style="{ '--avatar': colors[i % 8] }">{{
          initials(a)
        }}</span><span class="tag">{{
          a.npc ? "系统居民" : a.online ? "在线" : "离线"
        }}</span>
        <h2>{{ a.name }}</h2>
        <p>{{ a.activity }}</p>
        <div class="resident-card-stats">
          <span
            >精力 <strong>{{ a.energy }}</strong></span
          ><span
            >余额 <strong>{{ a.cash }}</strong></span
          ><span
            >已完成 <strong>{{ a.completed }}</strong></span
          >
        </div>
        <span class="card-link">在小镇中查看<ArrowUpRight :size="15" /></span>
      </button></div
  ></template>
</template>
