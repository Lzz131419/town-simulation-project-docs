import { computed } from "vue";
import { useTown } from "../stores/town";
export function useProgress() {
  const { me, catalog, world } = useTown();
  const progress = computed(
    () => me.value?.progress ?? { xp: 0, metrics: {}, badges: [] },
  );
  const level = computed(() => 1 + Math.floor(progress.value.xp / 100));
  const title = computed(
    () =>
      ["初来乍到", "生活学徒", "熟悉街坊", "社区合伙人", "河畔老邻居"][
        Math.min(4, level.value - 1)
      ],
  );
  const goals = computed(() =>
    (catalog.value.milestones ?? []).map((g) => ({
      ...g,
      value: Math.min(g.target, progress.value.metrics[g.metric] ?? 0),
      done: progress.value.badges.includes(g.id),
      unavailable:
        g.action === "contribute" &&
        !!world.value?.project.completed &&
        !progress.value.badges.includes(g.id),
    })),
  );
  const nextGoal = computed(() =>
    goals.value.find((g) => !g.done && !g.unavailable),
  );
  return { progress, level, title, goals, nextGoal };
}
