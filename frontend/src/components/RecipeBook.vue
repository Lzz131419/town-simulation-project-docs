<script setup lang="ts">
import { usePlanQueue } from "../composables/usePlanQueue";
import { computed, ref } from "vue";
import { ArrowRight, MapPin, Zap, Search } from "lucide-vue-next";
import { useTown } from "../stores/town";
import { invQty, itemNames } from "../types";
const emit = defineEmits<{ close: [] }>();
const { catalog, me, openPlace, action, pending } = useTown();
const { append } = usePlanQueue();
const group = ref("make"),
  search = ref("");
const groups = [
  { id: "make", name: "制作" },
  { id: "gather", name: "采集" },
  { id: "use", name: "饮食与恢复" },
];
const recipes = computed(() =>
  Object.entries(catalog.value.actions)
    .filter(([, a]) => a.inputs !== undefined)
    .map(([id, a]) => ({
      id,
      ...a,
      group: !a.outputs
        ? "use"
        : Object.keys(a.inputs ?? {}).length
          ? "make"
          : "gather",
    }))
    .filter(
      (a) =>
        a.group === group.value &&
        `${a.name} ${Object.keys(a.outputs ?? {})
          .map((k) => itemNames[k])
          .join(
            " ",
          )} ${a.place ? catalog.value.places[a.place]?.name : ""}`.includes(
          search.value.trim(),
        ),
    ),
);
function sources(item: string) {
  return Object.entries(catalog.value.actions)
    .filter(([, a]) => a.outputs?.[item] && a.place)
    .map(([id, a]) => ({
      id,
      place: a.place!,
      name: catalog.value.places[a.place!]?.name,
    }));
}
function visit(place: string) {
  emit("close");
  openPlace(place);
}
function use(id: string) {
  emit("close");
  void action({ type: id });
}
</script>
<template>
  <div class="recipe-book">
    <div class="recipe-toolbar">
      <div class="recipe-filters" role="group" aria-label="配方分类">
        <button
          v-for="g in groups"
          :key="g.id"
          :aria-pressed="group === g.id"
          @click="group = g.id"
        >
          {{ g.name }}
        </button>
      </div>
      <label class="recipe-search"
        ><Search :size="15" /><input
          v-model="search"
          aria-label="搜索配方"
          placeholder="搜索配方"
      /></label>
    </div>
    <div class="recipe-grid">
      <article v-for="r in recipes" :key="r.id" class="recipe-card">
        <div class="recipe-heading">
          <h3>{{ r.name }}</h3>
          <span><Zap :size="12" />{{ r.energy }}</span>
        </div>
        <div
          v-if="Object.keys(r.inputs ?? {}).length"
          class="recipe-ingredients"
        >
          <div
            v-for="(n, item) in r.inputs"
            :key="item"
            :class="{ missing: invQty(me?.inventory[item]) < n }"
          >
            <span>{{ itemNames[item] }}</span><strong
              >{{ invQty(me?.inventory[item]) }} / {{ n }}</strong
            >
          </div>
        </div>
        <p v-else class="recipe-no-input">无需原料</p>
        <div class="recipe-yield">
          <ArrowRight :size="14" /><span v-if="r.outputs">{{
            Object.entries(r.outputs)
              .map(([k, n]) => `${n} ${itemNames[k]}`)
              .join(" · ")
          }}</span
          ><span v-else
            >{{ r.hunger_relief ? `饥饿 −${r.hunger_relief}` : "" }}
            {{ r.energy_gain ? `精力 +${r.energy_gain}` : "" }}</span
          >
        </div>
        <p v-if="r.tool_bonus" class="recipe-tool">
          消耗 1 工具可多获得
          {{
            Object.entries(r.tool_bonus)
              .map(([k, n]) => `${n} ${itemNames[k]}`)
              .join(" · ")
          }}
        </p>
        <div v-for="(n, item) in r.inputs" :key="item" class="recipe-source">
          <template v-if="invQty(me?.inventory[item]) < n"
            ><span
              >缺 {{ n - invQty(me?.inventory[item]) }}
              {{ itemNames[item] }}</span
            ><button
              v-for="source in sources(String(item))"
              :key="source.id"
              @click="visit(source.place)"
            >
              {{ source.name }}<ArrowRight :size="11" /></button
          ></template>
        </div>
        <button v-if="r.place" class="recipe-location" @click="visit(r.place)">
          <MapPin :size="13" />{{ catalog.places[r.place]?.name
          }}<ArrowRight :size="13" />
        </button>
        <button
          v-else
          class="recipe-location"
          :disabled="
            pending ||
            Object.entries(r.inputs ?? {}).some(
              ([k, n]) => invQty(me?.inventory[k]) < n,
            )
          "
          @click="use(r.id)"
        >
          立即使用<ArrowRight :size="13" />
        </button>
        <button
          class="queue-add"
          :disabled="pending || (me?.plan?.length ?? 0) >= 8"
          @click="append({ type: r.id })"
        >
          加入计划 <span>{{ me?.plan?.length ?? 0 }} / 8</span>
        </button>
      </article>
    </div>
    <p v-if="!recipes.length" class="recipe-empty">没有找到相关配方</p>
  </div>
</template>
