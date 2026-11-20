<script setup lang="ts">
import { useTown } from "../stores/town";
import { Warehouse } from "lucide-vue-next";

const { user, world, pending, me, contribute, action, who } = useTown();
</script>
<template>
  <template v-if="world && me && user"
    ><div class="project-hero">
      <h2>{{ world.project.name }}</h2>
      <Warehouse class="project-symbol" :size="88" :stroke-width="1" />
      <span class="tag">{{
        world.project.completed
          ? "已落成 · 全员背包容量60份"
          : "建设中 · 建成后全员背包容量30 → 60份"
      }}</span>
    </div>
    <div class="two-col">
      <article class="card">
        <h2>建设进度</h2>
        <div
          v-for="x in [
            {
              label: '木材',
              value: world.project.wood,
              target: world.project.wood_target,
            },
            {
              label: '建设资金',
              value: world.project.cash,
              target: world.project.cash_target,
            },
          ]"
          class="project-progress"
        >
          <div>
            <span>{{ x.label }}</span><strong
              >{{ x.value }} / {{ x.target }}</strong
            >
          </div>
          <div class="progress-track">
            <i
              :style="{
                width: Math.min(100, (x.value / x.target) * 100) + '%',
              }"
            ></i>
          </div>
        </div>
        <form
          class="contribution-form"
          @submit.prevent="action({ type: 'contribute', ...contribute })"
        >
          <select v-model="contribute.item">
            <option value="wood">木材</option>
            <option value="cash">镇币</option></select
          ><input
            v-model.number="contribute.quantity"
            type="number"
            min="1"
            max="10"
          /><button
            class="primary"
            :disabled="world.project.completed || pending"
          >
            前往捐建
          </button>
        </form>
      </article>
      <article class="card">
        <h2>成员贡献</h2>
        <p v-if="!Object.keys(world.project.contributors).length" class="empty">
          暂无贡献
        </p>
        <div v-for="(n, id) in world.project.contributors" class="list-line">
          <span>{{ who(id) }}</span><strong>{{ n }} 贡献单位</strong>
        </div>
      </article>
    </div>
    <article class="card festival-card">
      <div>
        <h2>{{ world.activity_goal.name }}</h2>
        <p>交易次数</p>
      </div>
      <strong
        >{{ world.activity_goal.trades
        }}<small> / {{ world.activity_goal.target }}</small></strong
      ><span class="tag green">{{
        world.activity_goal.trades >= world.activity_goal.target
          ? "集市里程碑已达成"
          : "共同筹备中"
      }}</span>
    </article></template
  >
</template>
