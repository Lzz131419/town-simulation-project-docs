<script setup lang="ts">
import { useTown } from "../stores/town";
import { members } from "../types";

import { ArrowRight, Send, RefreshCw } from "lucide-vue-next";

const {
  user,
  world,
  pending,
  me,
  messages,
  messageForm,
  refreshMessages,
  sendMessage,
  who,
} = useTown();
</script>
<template>
  <template v-if="world && me && user"
    ><div class="two-col uneven">
      <article class="card">
        <div class="section-heading">
          <h2>留给彼此的话</h2>
          <button class="icon-button" title="刷新留言" @click="refreshMessages">
            <RefreshCw :size="16" />
          </button>
        </div>
        <p v-if="!messages.length" class="empty">暂无留言</p>
        <div
          v-for="m in messages"
          :key="m.id"
          class="message"
          :class="{ mine: m.sender_id === user.id }"
        >
          <div>
            <strong>{{ who(m.sender_id) }}</strong><ArrowRight
              :size="12"
            /><span>{{ who(m.recipient_id) }}</span
            ><small>{{ new Date(m.created_at).toLocaleString("zh-CN") }}</small>
          </div>
          <p>{{ m.text }}</p>
        </div>
      </article>
      <form class="card sticky-card" @submit.prevent="sendMessage">
        <h2>发送留言</h2>
        <label
          >收件人<select v-model="messageForm.recipient_id">
            <option
              v-for="m in members.filter((m) => m.id !== user!.id)"
              :value="m.id"
            >
              {{ m.name }}
            </option>
          </select></label
        ><label
          >想说的话<textarea
            v-model="messageForm.text"
            maxlength="500"
            rows="7"
            placeholder="输入留言内容"
            required
          ></textarea></label
        ><button class="primary wide" :disabled="pending">
          <Send :size="16" />发送留言
        </button>
      </form>
    </div></template
  >
</template>
