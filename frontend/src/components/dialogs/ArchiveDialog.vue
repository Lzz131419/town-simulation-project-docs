<script setup lang="ts">
import { useTown } from "../../stores/town";
import { gameTime } from "../../types";
import { api } from "../../api";
import { X, Download } from "lucide-vue-next";

const { user, archiveDetail, perform, downloadArchive } = useTown();
</script>
<template>
  <div
    v-if="archiveDetail && user"
    class="modal-backdrop"
    @click.self="archiveDetail = null"
  >
    <section class="modal">
      <button
        class="close-button"
        aria-label="关闭归档"
        @click="archiveDetail = null"
      >
        <X :size="20" />
      </button>
      <h2>{{ archiveDetail.title }}</h2>
      <p>
        {{ gameTime(archiveDetail.data.world.tick) }} ·
        {{ new Date(archiveDetail.created_at).toLocaleString("zh-CN") }}
      </p>
      <div class="card archive-summary">
        <strong>归档状态</strong>
        <p>
          余额 {{ archiveDetail.data.world.agents[user.id].cash }} 镇币 ·
          {{ archiveDetail.data.world.agents[user.id].plan.length }}
          步待执行计划
        </p>
        <p>{{ archiveDetail.data.profile.goal }}</p>
      </div>
      <p class="muted">
        恢复仅应用自己的计划与规则，并切回本人控制；资产、订单和其他居民保持现在的状态。
      </p>
      <div class="button-row">
        <button
          class="primary"
          @click="
            perform(
              () => api(`/archives/${archiveDetail.id}/restore-plan`, 'POST'),
              '个人计划与规则已恢复',
            )
          "
        >
          恢复个人计划</button
        ><button @click="downloadArchive">
          <Download :size="15" />导出快照
        </button>
      </div>
    </section>
  </div>
</template>
