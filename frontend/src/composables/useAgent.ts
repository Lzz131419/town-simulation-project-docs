import { ref } from "vue";
import { api } from "../api";
import type { Action, Policy } from "../types";
import type { FeatureContext } from "./context";
export function useAgent(ctx: FeatureContext) {
  const { myPlan, perform, refresh, notify } = ctx;
  const policy = ref<Policy>({
    reserve: 20,
    daily_budget: 20,
    fallback: "work",
    auto_eat: true,
  });
  const profile = ref({ bio: "", goal: "" });
  const model = ref<any>({ configured: false, calls: [] }),
    modelForm = ref({ base_url: "", model: "", api_key: "" }),
    prompt = ref(""),
    aiBusy = ref(false),
    aiResult = ref("");
  const planBase = ref<Action[]>([]);
  const planDraft = ref<Action[]>([]),
    planChoice = ref("farm");
  function syncPlanDraft() {
    planBase.value = myPlan.value.map((a) => ({ ...a }));
    planDraft.value = myPlan.value.map((a) => ({ ...a }));
  }
  async function savePlanDraft() {
    const epoch = generation;
    const expected = planBase.value.map((a) => ({ ...a }));
    const actions = planDraft.value.map((a) => ({ ...a }));
    await perform(async () => {
      await api("/me/plan/edit", "POST", { expected, actions });
      if (epoch === generation) planBase.value = actions;
    }, "行动计划已保存");
  }
  let generation = 0;
  let controller: AbortController | undefined;
  async function loadModel() {
    const epoch = generation;
    const data = await api("/model");
    if (epoch !== generation) return;
    model.value = data;
    modelForm.value = {
      base_url: model.value.base_url,
      model: model.value.model,
      api_key: "",
    };
  }
  async function saveModel() {
    const epoch = generation;
    await perform(async () => {
      await api("/model", "PUT", modelForm.value);
      if (epoch === generation) await loadModel();
    }, "模型配置已保存");
  }
  async function callAI(test = false) {
    if (aiBusy.value) return;
    aiBusy.value = true;
    aiResult.value = "";
    const epoch = generation;
    controller = new AbortController();
    try {
      const r = await api(
        test ? "/agent/test" : "/agent/plan",
        "POST",
        test ? undefined : { instruction: prompt.value },
        { timeoutMs: 40000, signal: controller.signal },
      );
      if (epoch !== generation) return;
      aiResult.value = r.summary;
      await refresh();
      if (epoch !== generation) return;
      syncPlanDraft();
      await loadModel();
      if (epoch !== generation) return;
      notify(test ? "连接测试成功" : "新计划已保存，启用托管后执行");
    } catch (e: any) {
      if (epoch === generation) notify(e.message, true);
    } finally {
      if (epoch === generation) aiBusy.value = false;
    }
  }
  function resetAgent() {
    generation++;
    controller?.abort();
    aiBusy.value = false;
    aiResult.value = "";
    model.value = { configured: false, calls: [] };
    modelForm.value = { base_url: "", model: "", api_key: "" };
    profile.value = { bio: "", goal: "" };
    prompt.value = "";
    planDraft.value = [];
    planBase.value = [];
    policy.value = {
      reserve: 20,
      daily_budget: 20,
      fallback: "work",
      auto_eat: true,
    };
  }
  return {
    resetAgent,
    syncPlanDraft,
    savePlanDraft,
    policy,
    profile,
    model,
    modelForm,
    prompt,
    aiBusy,
    aiResult,
    planDraft,
    planChoice,
    loadModel,
    saveModel,
    callAI,
  };
}
