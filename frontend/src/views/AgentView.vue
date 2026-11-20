<script setup lang="ts">
import { useTown } from "../stores/town";
import { actionNames } from "../types";
import { api } from "../api";
import {
  BrainCircuit,
  Play,
  Pause,
  Check,
  Plus,
  X,
  LoaderCircle,
} from "lucide-vue-next";

const {
  user,
  catalog,
  world,
  connected,
  pending,
  me,
  myPlan,
  policy,
  profile,
  model,
  modelForm,
  prompt,
  aiBusy,
  aiResult,
  planDraft,
  planChoice,
  syncPlanDraft,
  savePlanDraft,
  perform,
  control,
  loadModel,
  saveModel,
  callAI,
  actionText,
} = useTown();
</script>
<template>
  <template v-if="world && me && user">
    <div class="two-col">
      <div class="card">
        <div class="section-heading">
          <h2>我的目标与计划</h2>
          <span class="tag" :class="{ green: me.mode !== 'manual' }">{{
            me.mode === "rules"
              ? "持续托管"
              : me.mode === "plan"
                ? "执行本轮计划"
                : "本人控制"
          }}</span>
        </div>
        <label
          >人物简介<textarea
            v-model="profile.bio"
            rows="2"
            maxlength="500"
            placeholder="输入角色简介与偏好"
          ></textarea></label
        ><label
          >生活目标<textarea
            v-model="profile.goal"
            rows="2"
            maxlength="500"
          ></textarea></label
        ><button
          class="quiet"
          @click="perform(() => api('/me', 'PUT', profile), '个人目标已保存')"
        >
          保存目标<Check :size="15" />
        </button>
        <div class="form-divider"></div>
        <label
          >规划指令<textarea
            v-model="prompt"
            rows="3"
            maxlength="1500"
            placeholder="例如：先收获谷物，再烘焙面包，最后去广场。"
          ></textarea>
        </label>
        <div class="button-row">
          <button
            class="primary"
            :disabled="
              aiBusy || !connected || !model.configured || !prompt.trim()
            "
            @click="callAI()"
          >
            <LoaderCircle v-if="aiBusy" class="spin" :size="16" /><BrainCircuit
              v-else
              :size="16"
            />{{ aiBusy ? "正在制定计划" : "让 AI 制定计划" }}</button
          ><button v-if="aiBusy" @click="api('/agent/cancel', 'POST')">
            停止
          </button>
        </div>
        <p v-if="aiResult" class="ai-result">{{ aiResult }}</p>
        <div class="section-heading subheading">
          <h3>
            待执行计划 <span>{{ myPlan.length }} / 8</span>
          </h3>
          <button class="quiet compact" @click="syncPlanDraft()">同步</button>
        </div>
        <div v-for="(a, i) in planDraft" :key="i" class="plan-step">
          <span>{{ String(i + 1).padStart(2, "0") }}</span><strong>{{
            actionText(a)
          }}</strong
          ><button
            class="icon-button"
            title="移除此步骤"
            @click="planDraft.splice(i, 1)"
          >
            <X :size="14" />
          </button>
        </div>
        <div class="plan-add">
          <select v-model="planChoice">
            <option
              v-for="id in Object.keys(catalog.actions).filter(
                (id) =>
                  !['buy', 'sell', 'move', 'contribute', 'delivery'].includes(
                    id,
                  ),
              )"
              :key="id"
              :value="id"
            >
              {{ actionNames[id] }}
            </option></select
          ><button
            :disabled="planDraft.length >= 8"
            @click="planDraft.push({ type: planChoice })"
          >
            <Plus :size="15" />加入
          </button>
        </div>
        <div class="button-row">
          <button :disabled="pending" @click="savePlanDraft()">保存计划</button
          ><button
            :disabled="pending || !connected || !myPlan.length"
            @click="control('plan')"
          >
            <Play :size="14" />仅执行本轮</button
          ><button class="primary" @click="control('rules')">
            <Play :size="14" />执行计划与规则</button
          ><button v-if="me.mode !== 'manual'" @click="control('manual')">
            <Pause :size="14" />接管
          </button>
        </div>
      </div>
      <div class="stack-cards">
        <form class="card" @submit.prevent="saveModel">
          <div class="section-heading">
            <h2>连接我的模型</h2>
            <span class="tag" :class="{ green: model.configured }">{{
              model.configured ? "已配置" : "未配置"
            }}</span>
          </div>
          <label
            >API 地址<input
              v-model="modelForm.base_url"
              type="url"
              placeholder="https://服务域名/v1"
              required /></label
          ><label
            >模型名称<input
              v-model="modelForm.model"
              placeholder="服务商提供的模型 ID"
              required /></label
          ><label
            >API Key<input
              v-model="modelForm.api_key"
              type="password"
              autocomplete="off"
              :placeholder="
                model.has_key ? '已保存，留空保留现有 Key' : '输入你的 API Key'
              "
          /></label>
          <div class="button-row">
            <button class="primary" :disabled="pending">保存配置</button
            ><button
              type="button"
              :disabled="!model.configured || aiBusy || !connected"
              @click="callAI(true)"
            >
              测试连接</button
            ><button
              v-if="model.configured"
              type="button"
              class="quiet"
              @click="
                perform(async () => {
                  await api('/model', 'DELETE');
                  await loadModel();
                }, '模型配置已移除')
              "
            >
              移除
            </button>
          </div>
          <p class="muted">OpenAI 兼容接口；测试连接会调用一次模型。</p>
        </form>
        <form
          class="card"
          @submit.prevent="
            perform(
              () => api('/me/policy', 'PUT', policy),
              '离线执行规则已保存',
            )
          "
        >
          <h2>托管规则</h2>
          <div class="two-fields">
            <label
              >至少保留镇币<input
                v-model.number="policy.reserve"
                type="number"
                min="0"
                max="10000" /></label
            ><label
              >每日自主支出上限<input
                v-model.number="policy.daily_budget"
                type="number"
                min="0"
                max="500"
            /></label>
          </div>
          <label
            >计划结束后的安排<select v-model="policy.fallback">
              <option
                v-for="id in [
                  'work',
                  'farm',
                  'craft',
                  'bake',
                  'rest',
                  'social',
                  'gather',
                  'fish',
                  'chop',
                  'mine',
                  'forage',
                  'grill',
                  'forge',
                  'harvest_veg',
                  'gather_honey',
                  'harvest_flax',
                  'weave',
                  'assemble',
                  'cook',
                ]"
                :value="id"
              >
                {{ actionNames[id] }}
              </option>
            </select></label
          ><label class="checkbox-label"
            ><input
              v-model="policy.auto_eat"
              type="checkbox"
            />饥饿时自动吃饭或在预算内补给</label
          ><button :disabled="pending">保存规则<Check :size="15" /></button>
        </form>
      </div>
    </div>
    <article class="card usage-card">
      <h2>最近的模型调用</h2>
      <p v-if="!model.calls.length" class="empty">暂无调用记录</p>
      <div v-for="c in model.calls" class="list-line">
        <span
          >{{ new Date(c.created_at).toLocaleString("zh-CN") }} ·
          {{ c.purpose === "test" ? "连接测试" : "行动规划" }}</span
        ><span>{{
          (
            {
              running: "进行中",
              received: "收到响应",
              failed: "失败",
              cancelled: "已停止",
            } as any
          )[c.status] ?? c.status
        }}</span
        ><strong>{{
          c.usage_reported
            ? `${c.input_tokens} 输入 / ${c.output_tokens} 输出`
            : "用量未由服务商返回"
        }}</strong>
      </div>
    </article></template
  >
</template>
