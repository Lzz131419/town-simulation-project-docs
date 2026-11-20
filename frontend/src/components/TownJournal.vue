<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from "vue";
import { BookOpen, Check, ArrowUpRight, X, Award } from "lucide-vue-next";
import { useTown } from "../stores/town";
import RecipeBook from "./RecipeBook.vue";
import { useProgress } from "../composables/useProgress";
const emit = defineEmits<{ close: [] }>();
const { openPlace, go, world, me } = useTown();
const { progress, level, title, goals } = useProgress();
const tab = ref("goals");
const close = ref<HTMLButtonElement>();
function key(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}
onMounted(() => {
  close.value?.focus();
  window.addEventListener("keydown", key);
});
onBeforeUnmount(() => window.removeEventListener("keydown", key));
function visit(action: string, place: string) {
  emit("close");
  if (action === "order") go("orders");
  else openPlace(place);
}
</script>
<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <section
      class="modal town-journal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="journal-heading"
    >
      <button
        ref="close"
        class="close-button"
        aria-label="关闭生活手册"
        @click="emit('close')"
      >
        <X :size="20" />
      </button>
      <div class="journal-heading">
        <BookOpen :size="24" />
        <h2 id="journal-heading">生活手册</h2>
      </div>
      <div class="journal-tabs" role="group" aria-label="生活手册内容">
        <button :aria-pressed="tab === 'goals'" @click="tab = 'goals'">
          成长目标
        </button>
        <button :aria-pressed="tab === 'recipes'" @click="tab = 'recipes'">
          配方图鉴
        </button>
      </div>
      <RecipeBook v-if="tab === 'recipes'" @close="emit('close')" />
      <template v-else>
        <div class="journal-level">
          <span class="level-stamp">{{ level }}</span>
          <div>
            <strong>{{ title }}</strong>
            <p>
              {{ progress.xp }} 成长值 · 已达成 {{ progress.badges.length }} /
              {{ goals.length }}
            </p>
          </div>
          <Award :size="31" />
        </div>
        <div
          class="journal-xp"
          role="progressbar"
          aria-label="当前等级成长进度"
          :aria-valuenow="progress.xp % 100"
          :aria-valuemin="0"
          :aria-valuemax="100"
        >
          <i :style="{ width: (progress.xp % 100) + '%' }"></i>
        </div>
        <div class="journal-goals">
          <article
            v-for="(goal, i) in goals"
            :key="goal.id"
            :class="{ done: goal.done }"
          >
            <span class="goal-number"
              ><Check v-if="goal.done" :size="18" /><template v-else>{{
                String(i + 1).padStart(2, "0")
              }}</template></span
            >
            <div>
              <h3>{{ goal.name }}</h3>
              <p>{{ goal.description }}</p>
              <div class="goal-track">
                <i
                  :style="{ width: (goal.value / goal.target) * 100 + '%' }"
                ></i>
              </div>
            </div>
            <span v-if="goal.done" class="goal-achieved">已达成</span
            ><button
              v-else-if="!goal.unavailable"
              class="quiet compact"
              @click="visit(goal.action, goal.place)"
            >
              {{ goal.value }} / {{ goal.target }}<ArrowUpRight :size="15" />
            </button>
            <span v-if="goal.unavailable" class="goal-achieved"
              >本期建设已结束</span
            >
          </article>
        </div>
        <div v-if="world && me" class="journal-shared">
          <strong>{{
            world.project.completed ? "共享仓库已落成" : "共建 · 河畔共享仓库"
          }}</strong><span
            >我的贡献 {{ world.project.contributors[me.id] ?? 0 }}</span
          ><button
            class="quiet compact"
            @click="
              emit('close');
              go('project');
            "
          >
            查看建设<ArrowUpRight :size="14" />
          </button>
        </div>
      </template>
    </section>
  </div>
</template>
