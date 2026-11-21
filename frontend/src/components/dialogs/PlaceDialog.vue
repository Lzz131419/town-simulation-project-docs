<script setup lang="ts">
import DeliveryBoard from "../DeliveryBoard.vue";
import { layout } from "../../game/world-layout";
import { usePlanQueue } from "../../composables/usePlanQueue";
import { ref, watch } from "vue";
import { useTown } from "../../stores/town";
import { invQty, itemNames } from "../../types";
import { api } from "../../api";
import { ArrowRight, X, MapPin, Clock3, Zap } from "lucide-vue-next";
const { place, catalog, go, action, me, pending } = useTown();
const { append } = usePlanQueue();
const travel = ref<number | null>(null),
  routeError = ref("");
watch(place, async (id, _, onCleanup) => {
  travel.value = null;
  routeError.value = "";
  if (!id) return;
  const controller = new AbortController();
  onCleanup(() => controller.abort());
  try {
    const r = await api<{ seconds: number }>(
      `/me/route?place=${encodeURIComponent(id)}`,
      "GET",
      undefined,
      { signal: controller.signal },
    );
    if (!controller.signal.aborted) travel.value = r.seconds;
  } catch (e: any) {
    if (!controller.signal.aborted) routeError.value = e.message;
  }
});
const items = (values?: Record<string, number>) =>
  Object.entries(values ?? {})
    .map(([id, n]) => `${n} ${itemNames[id] ?? id}`)
    .join(" · ");
</script>
<template>
  <div v-if="place" class="modal-backdrop" @click.self="place = ''">
    <section
      class="modal place-modal"
      :class="{ 'depot-modal': place === 'depot' }"
      role="dialog"
      :aria-label="catalog.places[place]?.name"
    >
      <button class="close-button" aria-label="关闭地点" @click="place = ''">
        <X :size="20" />
      </button>
      <div class="place-eyebrow">
        <MapPin :size="15" />{{
          layout.districts.find((d) => d.id === catalog.places[place]?.district)
            ?.name ?? "中心街区"
        }}
      </div>
      <h2>{{ catalog.places[place]?.name }}</h2>
      <p class="place-travel">
        <Clock3 :size="14" />{{
          routeError ||
          (travel === null ? "正在查看路线…" : `步行约 ${Math.ceil(travel)} 秒`)
        }}
      </p>
      <DeliveryBoard v-if="place === 'depot'" />
      <div class="place-actions">
        <article
          v-for="[id, a] in Object.entries(catalog.actions).filter(
            ([id, a]) => a.place === place && id !== 'delivery',
          )"
          :key="id"
          class="place-action-card"
        >
          <div class="place-action-heading">
            <strong>{{ a.name }}</strong><span
              ><Zap :size="12" />{{ a.energy }} 精力</span
            >
          </div>
          <p v-if="a.inputs && Object.keys(a.inputs).length">
            消耗 {{ items(a.inputs) }}
          </p>
          <p v-if="a.outputs">获得 {{ items(a.outputs) }}</p>
          <p v-if="a.hunger_relief || a.energy_gain">
            {{ a.hunger_relief ? `饥饿 −${a.hunger_relief}` : "" }}
            {{ a.energy_gain ? `精力 +${a.energy_gain}` : "" }}
          </p>
          <p v-if="a.tool_bonus" class="place-bonus">
            携带工具时消耗 1 工具，额外获得 {{ items(a.tool_bonus) }}
          </p>
          <p
            v-if="
              a.inputs &&
              Object.entries(a.inputs).some(
                ([k, n]) => invQty(me?.inventory[k]) < n,
              )
            "
            class="place-shortage"
          >
            当前原料不足
          </p>
          <button
            class="primary"
            :disabled="pending || !!routeError"
            @click="
              id === 'buy' || id === 'sell'
                ? go('market')
                : id === 'contribute'
                  ? go('project')
                  : action({ type: id });
              place = '';
            "
          >
            {{
              id === "buy" || id === "sell"
                ? "前往集市页面"
                : id === "contribute"
                  ? "查看共建"
                  : "安排此行动"
            }}<ArrowRight :size="15" />
          </button>
          <button
            v-if="!['buy', 'sell', 'contribute'].includes(id)"
            class="queue-add"
            :disabled="pending || (me?.plan?.length ?? 0) >= 8"
            @click="append({ type: id })"
          >
            加入计划 <span>{{ me?.plan?.length ?? 0 }} / 8</span>
          </button>
        </article>
        <button
          :disabled="pending || !!routeError"
          @click="action({ type: 'move', place })"
        >
          <MapPin :size="15" />仅前往此处
        </button>
      </div>
    </section>
  </div>
</template>
