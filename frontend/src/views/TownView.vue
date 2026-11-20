<script setup lang="ts">
import { ref } from "vue";
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
} = useTown();
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
