<script setup lang="ts">
import { useTown } from "../stores/town";
import { gameTime } from "../types";
import { api } from "../api";
import { Cloud, ArrowUpRight, Plus, Trash2 } from "lucide-vue-next";

const {
  user,
  world,
  pending,
  me,
  archives,
  archiveTitle,
  perform,
  archive,
  showArchive,
} = useTown();
</script>
<template>
  <template v-if="world && me && user">
    <div class="archive-toolbar">
      <input
        v-model="archiveTitle"
        maxlength="80"
        placeholder="输入归档名称"
      /><button class="primary" :disabled="pending" @click="archive">
        <Plus :size="16" />创建个人归档
      </button>
    </div>
    <div class="resident-cards">
      <article v-for="a in archives" class="card archive-card">
        <Cloud :size="26" class="green-text" /><span class="eyebrow">{{
          gameTime(a.tick)
        }}</span>
        <h2>{{ a.title }}</h2>
        <p>{{ new Date(a.created_at).toLocaleString("zh-CN") }}</p>
        <div class="button-row">
          <button @click="showArchive(a.id)">
            查看归档<ArrowUpRight :size="14" /></button
          ><button
            class="quiet"
            title="删除归档"
            @click="
              perform(async () => {
                await api(`/archives/${a.id}`, 'DELETE');
                archives = await api('/archives');
              }, '归档已删除')
            "
          >
            <Trash2 :size="16" />
          </button>
        </div>
      </article>
    </div>
    <div v-if="!archives.length" class="card empty">暂无个人归档</div></template
  >
</template>
