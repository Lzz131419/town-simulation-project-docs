<script setup lang="ts">
import { computed, ref } from "vue";
import { useTown } from "../stores/town";

import { MessagesSquare, ArrowUpRight, BookOpen, Award } from "lucide-vue-next";
import TownMap from "../components/TownMap.vue";
import TownJourney from "../components/TownJourney.vue";
import TownInspector from "../components/TownInspector.vue";
import TownJournal from "../components/TownJournal.vue";
import { useProgress } from "../composables/useProgress";
const journal = ref(false);
const { level, nextGoal } = useProgress();

const {
  catalog,
  user,
  world,
  events,
  selected,
  focus,
  me,
  go,
  selectResident,
  openPlace,
  action,
  pending,
} = useTown();
const invitations = computed(() =>
  Object.values(world.value?.family_state?.invitations ?? {}).filter(
    (i) =>
      i.guest_id === user.value?.id &&
      i.status === "pending" &&
      (world.value?.tick ?? 0) <= i.expires_tick,
  ),
);
</script>
<template>
  <template v-if="world && me && user">
    <div class="town-page">
      <section class="map-side">
        <div class="page-heading">
          <h1>小镇生活</h1>
          <div class="town-heading-actions">
            <button class="journal-entry" @click="journal = true">
              <BookOpen :size="16" />生活手册<span>{{ level }}</span>
            </button>
            <button class="quiet" @click="go('messages')">
              <MessagesSquare :size="16" />邻里留言<ArrowUpRight :size="14" />
            </button>
          </div>
        </div>
        <TownMap
          :world="world"
          :self="user.id"
          :selected="selected"
          :catalog="catalog"
          :events="events"
          @select="selectResident"
          @place="openPlace"
          @expand="focus = !focus"
        />
        <div
          v-if="world.flood_effort && !world.flood_effort.settled"
          class="flood-banner"
          role="status"
        >
          <strong>暴雨预警 · 防洪筑堤进行中</strong>
          <span
            >筑堤进度 {{ world.flood_effort.donated }}/{ world.flood_effort.goal
            }} · 请前往共建事务所加固河堤</span
          >
        </div>
        <div
          v-for="invite in invitations"
          :key="invite.group"
          class="family-invite-banner"
          role="status"
        >
          <strong
            >{{ world.agents[invite.host_id]?.name }}邀请你到家里做客</strong
          >
          <span
            >{{ invite.home_id }} · 剩余
            {{ invite.expires_tick - world.tick }} tick</span
          >
          <button
            :disabled="pending"
            @click="action({ type: 'visit', target_id: invite.host_id })"
          >
            前去赴约
          </button>
        </div>
        <TownJourney
          ><button v-if="focus" class="quiet compact" @click="focus = false">
            退出大地图
          </button></TownJourney
        >
        <div class="live-strip">
          <button class="current-goal" @click="journal = true">
            <Award :size="15" /><span>{{
              nextGoal ? nextGoal.name : "生活手册"
            }}</span>
          </button>
          <p>{{ events[0]?.text }}</p>
          <button @click="go('report')"><ArrowUpRight :size="16" /></button>
        </div>
      </section>
      <TownInspector />
      <TownJournal v-if="journal" @close="journal = false" />
    </div>
  </template>
</template>

<style scoped>
.family-invite-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-top: 10px;
  border: 1px solid #c6a566;
  border-radius: 10px;
  background: #fff2d4;
  color: #57452c;
}
.family-invite-banner span {
  flex: 1;
  font-size: 12px;
}
</style>
