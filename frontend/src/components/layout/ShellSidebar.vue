<script setup lang="ts">
import { useTown } from "../../stores/town";
import { members } from "../../types";

import { Trees, LogOut, ChevronRight } from "lucide-vue-next";

const { user, connected, view, selected, nav, me, online, colors, logout, go } =
  useTown();
</script>
<template>
  <template v-if="user && me">
    <aside class="sidebar">
      <a class="brand" @click="go('town')"
        ><span class="brand-mark"><Trees :size="23" /></span
        ><span>雾河镇</span></a
      >
      <div class="workspace-label">小镇工作区</div>
      <nav>
        <button
          v-for="n in nav"
          :key="n.id"
          :class="{ active: view === n.id }"
          @click="go(n.id)"
        >
          <component :is="n.icon" :size="18" /><span>{{ n.label }}</span
          ><ChevronRight v-if="view === n.id" :size="14" />
        </button>
      </nav>
      <div class="sidebar-bottom">
        <div class="world-live">
          <span class="status-dot" :class="{ gray: !connected }"></span
          >{{ connected ? "共享世界已连接" : "正在重新连接"
          }}<span>{{ online }} / 6</span>
        </div>
        <button
          class="account"
          @click="
            selected = user.id;
            go('town');
          "
        >
          <span
            class="avatar small"
            :style="{
              '--avatar': colors[members.findIndex((m) => m.id === user!.id)],
            }"
            >{{ user.name.slice(-1) }}</span><span
            ><strong>{{ user.name }}</strong
            ><small>{{
              me.mode === "rules"
                ? "计划与规则托管"
                : me.mode === "plan"
                  ? "执行本轮计划"
                  : "本人控制"
            }}</small></span
          ></button
        ><button class="logout" @click="logout">
          <LogOut :size="15" />退出登录
        </button>
      </div>
    </aside>
  </template>
</template>
