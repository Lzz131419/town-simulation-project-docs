<script setup lang="ts">
import { computed, ref } from "vue";
import {
  Leaf,
  ClipboardList,
  Home,
  BrainCircuit,
  ChevronRight,
  Send,
  MessagesSquare,
  Check,
} from "lucide-vue-next";
import { useTown } from "../stores/town";
import { invQty, itemNames } from "../types";
const {
  person,
  user,
  colors,
  world,
  me,
  selected,
  initials,
  action,
  go,
  messageForm,
  pending,
  catalog,
} = useTown();
const showAll = ref(false);
const home = computed(() =>
  world.value?.homes?.find((h) => h.id === person.value?.home_id),
);
const housemates = computed(() =>
  Object.values(world.value?.agents ?? {}).filter(
    (a) => home.value && a.home_id === home.value.id,
  ),
);
const relatives = computed(() =>
  Object.values(world.value?.agents ?? {})
    .filter(
      (a) =>
        a.id !== person.value?.id &&
        person.value?.family?.group &&
        a.family?.group === person.value.family.group,
    )
    .map(
      (a) =>
        `${a.name}（${a.family?.kin === "spouse" ? (a.id === "npc-5" ? "妻子" : "丈夫") : "家人"}）`,
    )
    .join("、"),
);
const homeCost = computed(() =>
  home.value
    ? catalog.value.rules?.homes?.upgrades[String(home.value.level)]
    : undefined,
);
const homeCapacity = computed(
  () =>
    (world.value?.project.completed ? 60 : 30) +
    (home.value?.level ?? 0) *
      (catalog.value.rules?.homes?.capacity_per_level ?? 10),
);
const personalityNames: Record<string, string> = {
  introvert: "内向",
  diligent: "勤劳",
  merchant: "精明",
  generous: "慷慨",
  sociable: "随和",
  quiet: "安静",
};
const recentMemories = computed(() =>
  (person.value?.memories ?? []).slice(-3).reverse(),
);
const inventoryCount = computed(() =>
  Object.values(person.value?.inventory ?? {}).reduce<number>(
    (sum, value) => sum + invQty(value),
    0,
  ),
);
const inventory = computed(() =>
  Object.entries(person.value?.inventory ?? {})
    .map(([id, value]) => [id, invQty(value)] as const)
    .filter(([, n]) => showAll.value || n > 0),
);
const food = computed(() =>
  Object.entries(catalog.value.actions)
    .filter(
      ([, a]) => !a.place && a.inputs && (a.hunger_relief || a.energy_gain),
    )
    .map(([id, a]) => ({
      id,
      ...a,
      available: Object.entries(a.inputs!).every(
        ([k, n]) => invQty(me.value?.inventory[k]) >= n,
      ),
    })),
);
</script>
<template>
  <template v-if="world && me && user"
    ><aside v-if="person" class="inspector">
      <div class="inspector-top">
        <span>{{
          person.id === user.id ? "我的数字居民" : "正在观察"
        }}</span><span
          class="resident-presence"
          :class="{ online: person.online }"
          >{{ person.npc ? "小镇居民" : person.online ? "在线" : "离线" }}</span
        >
      </div>
      <div class="resident-hero">
        <div
          class="avatar large"
          :style="{
            '--avatar':
              colors[Object.keys(world.agents).indexOf(person.id) % 8],
          }"
        >
          {{ initials(person) }}
        </div>
        <h2>
          {{ person.title ? `${person.title} ${person.name}` : person.name }}
        </h2>
        <p>{{ person.activity }}</p>
      </div>
      <section
        v-if="person.npc"
        class="resident-memories"
        aria-label="个性与近况"
      >
        <div class="resident-relationship">
          <span>个性</span>
          <strong>{{
            personalityNames[person.personality ?? ""] ?? "随和"
          }}</strong>
        </div>
        <div class="resident-relationship">
          <span>家人</span><strong>{{ relatives || "独居" }}</strong>
        </div>
        <div class="section-label">最近的记忆</div>
        <ul v-if="recentMemories.length">
          <li v-for="(memory, index) in recentMemories" :key="index">
            {{ memory.text }}
          </li>
        </ul>
        <p v-else>还没有新的故事</p>
      </section>
      <div class="needs">
        <div :class="{ 'needs-warning': person.energy < 25 }">
          <span>精力</span>
          <div><i :style="{ width: person.energy + '%' }"></i></div>
          <strong>{{ person.energy }}</strong>
        </div>
        <div class="hunger" :class="{ 'needs-warning': person.hunger >= 80 }">
          <span>饥饿</span>
          <div><i :style="{ width: person.hunger + '%' }"></i></div>
          <strong>{{ person.hunger }}</strong>
        </div>
      </div>
      <section class="resident-memories" aria-label="家园">
        <strong>{{
          home ? `${person.name}的家 · ${home.level} 级` : "尚未安家"
        }}</strong>
        <p v-if="home">住户：{{ housemates.map((a) => a.name).join("、") }}</p>
        <p v-if="home">
          个人容量 {{ homeCapacity }} 份 · 睡眠恢复 ×{{
            catalog.rules?.homes?.sleep_multipliers[home.level - 1] ?? 1
          }}
        </p>
        <p v-else>首次回家休息时认领空住宅，满员后在广场长椅休息。</p>
        <p v-if="home?.level === 3">
          家中存粮：每日黎明饥饿 −{{
            catalog.rules?.homes?.dawn_hunger_relief ?? 5
          }}
        </p>
        <button
          v-if="person.id === user.id && homeCost"
          :disabled="
            pending ||
            !!person.sleeping ||
            person.cash < homeCost.cash ||
            invQty(person.inventory.wood) < homeCost.wood
          "
          @click="action({ type: 'upgrade_home' })"
        >
          升级家园 · {{ homeCost.wood }} 木材 + {{ homeCost.cash }} 镇币
        </button>
      </section>
      <div class="wallet">
        <span>个人余额</span
        ><strong>{{ person.cash }} <small>镇币</small></strong>
      </div>
      <button class="inventory-toggle" @click="showAll = !showAll">
        {{ showAll ? "收起空物资" : "查看全部物资"
        }}<span>{{ inventoryCount }} 份</span>
      </button>
      <div class="bag-grid">
        <div v-for="[id, n] in inventory" :key="id">
          <span>{{ itemNames[id] }}</span><strong>{{ n }}</strong>
        </div>
      </div>
      <div
        v-if="person.id === user.id"
        class="bag-food"
        role="group"
        aria-label="背包食物"
      >
        <button
          v-for="f in food"
          :key="f.id"
          :disabled="pending || !f.available"
          :title="`接管并使用 · 饥饿 −${f.hunger_relief ?? 0}${f.energy_gain ? ' · 精力 +' + f.energy_gain : ''}`"
          @click="action({ type: f.id })"
        >
          {{ f.name }}
        </button>
      </div>
      <template v-if="person.id === user.id"
        ><div class="section-label">安排接下来的行动</div>
        <div class="quick-actions">
          <button @click="action({ type: 'farm' })">
            <Leaf :size="17" />去农场</button
          ><button @click="action({ type: 'work' })">
            <ClipboardList :size="17" />做工作</button
          ><button @click="action({ type: 'rest' })">
            <Home :size="17" />回家休息
          </button>
        </div>
        <button class="ai-entry" @click="go('agent')">
          <BrainCircuit :size="21" /><span><strong>我的 AI 分身</strong></span
          ><ChevronRight :size="16" /></button></template
      ><template v-else>
        <div class="resident-relationship">
          <span>与我的关系</span
          ><strong>{{
            me.relations[person.id] === undefined
              ? "尚未交流"
              : "熟悉度 " + me.relations[person.id]
          }}</strong>
        </div>
        <button
          class="wide neighbor-greet"
          @click="action({ type: 'social', target_id: person.id })"
        >
          <MessagesSquare :size="16" />前去与{{ person.name }}交流
        </button>
        <button
          v-if="home && (me.relations[person.id] ?? 30) >= 40"
          class="wide neighbor-greet"
          :disabled="pending"
          @click="action({ type: 'visit', target_id: person.id })"
        >
          去家里做客
        </button>
        <button
          v-if="!person.npc"
          class="primary wide"
          @click="
            messageForm.recipient_id = person.id;
            go('messages');
          "
        >
          <Send :size="15" />给{{ person.name }}留言
        </button></template
      >
      <div class="section-label">
        小镇伙伴 <span>{{ Object.keys(world.agents).length }}</span>
      </div>
      <div class="inspector-roster">
        <button
          v-for="(a, i) in Object.values(world.agents)"
          :key="a.id"
          :class="{ selected: selected === a.id }"
          :aria-pressed="selected === a.id"
          @click="selected = a.id"
        >
          <span class="avatar tiny" :style="{ '--avatar': colors[i % 8] }">{{
            initials(a)
          }}</span><span>{{ a.title ? `${a.title} ${a.name}` : a.name }}</span>
          <span class="roster-state">
            <Check v-if="selected === a.id" :size="14" aria-label="已选中" />
            <i v-if="a.online" class="status-dot"></i>
            <small v-else>{{ a.npc ? "居民" : "离线" }}</small>
          </span>
        </button>
      </div>
    </aside></template
  >
</template>

<style scoped>
.resident-memories ul {
  margin: 0 0 16px;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.6;
}
.resident-memories li + li {
  margin-top: 6px;
}
.resident-memories p {
  margin: 0 0 16px;
  color: #666;
  font-size: 12px;
}
</style>
