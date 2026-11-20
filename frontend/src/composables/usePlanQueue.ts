import { api } from "../api";
import { useTown } from "../stores/town";
import type { Action } from "../types";

export function usePlanQueue() {
  const { me, perform, refresh } = useTown();
  const append = (action: Action) =>
    perform(
      () => api("/me/plan/append", "POST", { actions: [action] }),
      "已加入待执行计划",
    );
  async function edit(index: number, destination?: number) {
    const expected = (me.value?.plan ?? []).map((a) => ({ ...a }));
    if (!expected[index]) return;
    const actions = [...expected];
    const [step] = actions.splice(index, 1);
    if (destination !== undefined) actions.splice(destination, 0, step);
    await perform(
      async () => {
        try {
          await api("/me/plan/edit", "POST", { expected, actions });
        } catch (error) {
          await refresh();
          throw error;
        }
      },
      destination === undefined ? "已移除待执行步骤" : "计划顺序已更新",
    );
  }
  return { append, edit };
}
