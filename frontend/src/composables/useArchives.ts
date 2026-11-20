import { ref } from "vue";
import { api } from "../api";

import type { FeatureContext } from "./context";
export function useArchives(ctx: FeatureContext) {
  const { world, perform, notify } = ctx;
  const archives = ref<any[]>([]),
    archiveTitle = ref(""),
    archiveDetail = ref<any>(null);
  let generation = 0;
  function resetArchives() {
    generation++;
    archives.value = [];
    archiveDetail.value = null;
    archiveTitle.value = "";
  }
  async function archive() {
    const epoch = generation;
    await perform(async () => {
      await api("/archives", "POST", {
        title:
          archiveTitle.value ||
          `我的第${Math.floor(world.value!.tick / 144) + 1}天`,
      });
      if (epoch !== generation) return;
      const rows = await api("/archives");
      if (epoch !== generation) return;
      archives.value = rows;
      archiveTitle.value = "";
    }, "归档已保存到服务器");
  }
  async function showArchive(id: number) {
    const epoch = generation;
    try {
      const data = await api(`/archives/${id}`);
      if (epoch === generation) archiveDetail.value = data;
    } catch (e: any) {
      if (epoch === generation) notify(e.message, true);
    }
  }
  function downloadArchive() {
    const blob = new Blob([JSON.stringify(archiveDetail.value, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `town-archive-${archiveDetail.value.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  return {
    resetArchives,
    archives,
    archiveTitle,
    archiveDetail,
    archive,
    showArchive,
    downloadArchive,
  };
}
