<script setup lang="ts">
import { useTown } from "../../stores/town";

import { ArrowRight, X } from "lucide-vue-next";

const { returnSummary, user } = useTown();
</script>
<template>
  <div
    v-if="returnSummary && user"
    class="modal-backdrop"
    @click.self="returnSummary = null"
  >
    <section class="modal">
      <button
        class="close-button"
        aria-label="关闭离线记录"
        @click="returnSummary = null"
      >
        <X :size="20" />
      </button>
      <h2>欢迎回来，{{ user.name }}。</h2>
      <p>
        你离开期间，分身完成了 {{ returnSummary.completed }} 次行动，余额变化
        {{ returnSummary.cash_change >= 0 ? "+" : ""
        }}{{ returnSummary.cash_change }} 镇币。
      </p>
      <div class="card archive-summary">
        <p v-for="line in returnSummary.recent">{{ line }}</p>
      </div>
      <button class="primary" @click="returnSummary = null">
        继续我的生活<ArrowRight :size="16" />
      </button>
    </section>
  </div>
</template>
