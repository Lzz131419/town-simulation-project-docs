import { ref } from "vue";
import { api, ApiError } from "../api";
import type { TownEvent } from "../types";
export function useReports(notify: (text: string, isError?: boolean) => void) {
  const report = ref<any>(null),
    history = ref<TownEvent[]>([]),
    eventActor = ref(""),
    eventKind = ref("");
  let version = 0,
    reportVersion = 0,
    controller: AbortController | undefined,
    loadingMore = false;
  async function loadReport() {
    const epoch = ++reportVersion;
    try {
      const data = await api("/report");
      if (epoch === reportVersion) report.value = data;
    } catch (e: any) {
      if (epoch === reportVersion) notify(e.message, true);
    }
  }
  async function loadEvents(more = false) {
    if (more && loadingMore) return;
    if (!more) {
      controller?.abort();
      loadingMore = false;
    }
    const epoch = ++version;
    controller = new AbortController();
    loadingMore = more;
    const before =
      more && history.value.length ? history.value.at(-1)!.id : 2147483647;
    const query = new URLSearchParams({
      actor_id: eventActor.value,
      kind: eventKind.value,
      before: String(before),
    });
    try {
      const rows = await api<TownEvent[]>(
        `/events?${query}`,
        "GET",
        undefined,
        { signal: controller.signal },
      );
      if (epoch === version)
        history.value = more
          ? [
              ...new Map(
                [...history.value, ...rows].map((e) => [e.id, e]),
              ).values(),
            ]
          : rows;
    } catch (e: any) {
      if (
        epoch === version &&
        !(e instanceof ApiError && e.code === "cancelled")
      )
        notify(e.message, true);
    } finally {
      if (epoch === version) loadingMore = false;
    }
  }
  function resetReports() {
    version++;
    reportVersion++;
    controller?.abort();
    loadingMore = false;
    report.value = null;
    history.value = [];
    eventActor.value = "";
    eventKind.value = "";
  }
  return {
    report,
    history,
    eventActor,
    eventKind,
    loadEvents,
    loadReport,
    resetReports,
  };
}
