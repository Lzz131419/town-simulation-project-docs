<script setup lang="ts">
import { ref } from "vue";
import { useTown } from "../stores/town";
import { members } from "../types";
import {
  Trees,
  ArrowRight,
  LoaderCircle,
  Check,
  Eye,
  EyeOff,
} from "lucide-vue-next";
import LoginTownArtwork from "../components/LoginTownArtwork.vue";
import SketchMark from "../components/SketchMark.vue";

const { pending, loginForm, login } = useTown();
const showPassword = ref(false);
</script>
<template>
  <main class="login-screen">
    <section class="login-landscape">
      <div class="login-brand">
        <Trees :size="25" :stroke-width="1.6" /><span>雾河镇</span>
      </div>
      <div class="login-visual-content">
        <h1>你好，<br /><span>邻居。</span><SketchMark /></h1>
        <LoginTownArtwork />
        <SketchMark kind="dots" class="login-dots" />
      </div>
    </section>
    <section class="login-side">
      <form class="login-card" @submit.prevent="login">
        <header class="login-heading"><h2>登录小镇</h2></header>
        <fieldset class="resident-picker">
          <legend>选择居民</legend>
          <div class="member-grid">
            <button
              v-for="m in members"
              :key="m.id"
              type="button"
              :aria-pressed="loginForm.username === m.id"
              :class="{ chosen: loginForm.username === m.id }"
              @click="loginForm.username = m.id"
            >
              <span class="member-initial">{{ m.name.slice(-1) }}</span>
              <span class="member-name">{{ m.name }}</span>
              <Check
                v-if="loginForm.username === m.id"
                class="member-check"
                :size="13"
              />
            </button>
          </div>
        </fieldset>
        <label for="town-username">用户名</label>
        <input
          id="town-username"
          v-model="loginForm.username"
          name="username"
          autocomplete="username"
          required
        />
        <label for="town-password">密码</label>
        <div class="password-field">
          <input
            id="town-password"
            v-model="loginForm.password"
            name="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            required
          />
          <button
            type="button"
            class="password-toggle"
            :aria-label="showPassword ? '隐藏密码' : '显示密码'"
            @click="showPassword = !showPassword"
          >
            <EyeOff v-if="showPassword" :size="18" /><Eye v-else :size="18" />
          </button>
        </div>
        <button class="primary login-submit" :disabled="pending">
          <span
            ><LoaderCircle v-if="pending" :size="18" class="spin" />{{
              pending ? "正在进入" : "进入雾河镇"
            }}</span
          ><ArrowRight :size="19" />
        </button>
      </form>
    </section>
  </main>
</template>
