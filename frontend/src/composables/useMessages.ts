import { ref } from "vue";
import { api } from "../api";
import type { FeatureContext } from "./context";
export function useMessages(ctx: FeatureContext) {
  const messages = ref<any[]>([]),
    messageForm = ref({ recipient_id: "zhangguo", text: "" });
  let generation = 0;
  async function refreshMessages() {
    const epoch = ++generation;
    try {
      const rows = await api("/messages");
      if (epoch === generation) messages.value = rows;
    } catch (e: any) {
      if (epoch === generation) ctx.notify(e.message, true);
    }
  }
  async function sendMessage() {
    const epoch = generation;
    await ctx.perform(async () => {
      await api("/messages", "POST", { ...messageForm.value });
      if (epoch !== generation) return;
      messageForm.value.text = "";
      await refreshMessages();
    }, "留言已送达");
  }
  function resetMessages() {
    generation++;
    messages.value = [];
    messageForm.value = { recipient_id: "zhangguo", text: "" };
  }
  return { messages, messageForm, refreshMessages, sendMessage, resetMessages };
}
