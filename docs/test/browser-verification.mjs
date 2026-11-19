import { createSimulation, SCENARIO } from "../../src/app/simulation.mjs";
const encoder = new TextEncoder(),
  profile = {
    profileVersion: 1,
    displayName: "<b>林溪</b>",
    authorizationConfirmed: true,
    bioSummary: "虚构测试人物",
  },
  bytes = (x) => encoder.encode(JSON.stringify(x));
function command(app, type, payload = {}) {
  const r = app.dispatch({
    type,
    payload,
    expectedRevision: app.runtime.runtimeRevision,
  });
  if (!r.ok) throw Error(JSON.stringify(r));
  return r;
}
function assert(condition, message) {
  if (!condition) throw Error(message);
}
const frame = () =>
  new Promise((resolve) =>
    requestAnimationFrame(() => requestAnimationFrame(resolve)),
  );
function summarize(samples, limit) {
  const sorted = [...samples].sort((a, b) => a - b);
  return {
    samplesMs: samples,
    p95Ms: sorted[Math.ceil(sorted.length * 0.95) - 1],
    targetMs: limit,
    pass: sorted[Math.ceil(sorted.length * 0.95) - 1] <= limit,
  };
}
document.getElementById("verify").onclick = async () => {
  const out = document.getElementById("result"),
    button = document.getElementById("verify");
  button.disabled = true;
  try {
    out.textContent = "运行中";
    const a = createSimulation();
    command(a, "CREATE_WORLD", { config: SCENARIO });
    command(a, "IMPORT_PROFILE", { utf8Bytes: bytes(profile) });
    for (let i = 0; i < 7; i++) command(a, "STEP");
    command(a, "TRIGGER_SHORTAGE");
    command(a, "CLOSE_VOTE", { proposalId: "repair-well-01" });
    command(a, "EXECUTE_PROPOSAL", {
      proposalId: "repair-well-01",
      proposalVersion: 1,
    });
    for (let i = 7; i < 29; i++) command(a, "STEP");
    const baseline = a.exportSnapshot().data.json,
      baselineBytes = encoder.encode(baseline);
    const steps = [],
      restores = [],
      profiles = [],
      ui = [];
    for (let i = 0; i < 110; i++) {
      let start = performance.now();
      command(a, "IMPORT_SNAPSHOT", { utf8Bytes: baselineBytes });
      const restore = performance.now() - start;
      start = performance.now();
      command(a, "STEP");
      const step = performance.now() - start;
      const b = createSimulation();
      command(b, "CREATE_WORLD", { config: SCENARIO });
      const padded = encoder.encode(
        JSON.stringify(profile) + " ".repeat(16384 - bytes(profile).length),
      );
      start = performance.now();
      command(b, "IMPORT_PROFILE", { utf8Bytes: padded });
      const profileMs = performance.now() - start;
      if (i >= 10) {
        steps.push(step);
        restores.push(restore);
        profiles.push(profileMs);
      }
      if (i % 10 === 0) await frame();
    }
    const iframe = document.getElementById("product"),
      doc = iframe.contentDocument,
      win = iframe.contentWindow;
    if (!doc.getElementById("day").textContent.trim())
      doc.getElementById("create").click();
    doc.getElementById("profile-text").value = JSON.stringify(profile);
    doc.getElementById("profile-import").click();
    doc.getElementById("agent-select").value = "digital-001";
    doc
      .getElementById("agent-select")
      .dispatchEvent(new win.Event("change", { bubbles: true }));
    assert(
      doc.getElementById("agent-detail").textContent.includes("<b>林溪</b>"),
      "名称文本未显示",
    );
    assert(
      !doc.getElementById("agent-detail").querySelector("b"),
      "名称被解释为HTML",
    );
    const restoreUI = async () => {
      const input = doc.getElementById("snapshot-file"),
        transfer = new win.DataTransfer();
      transfer.items.add(
        new win.File([baseline], "day29.json", { type: "application/json" }),
      );
      input.files = transfer.files;
      input.dispatchEvent(new win.Event("change", { bubbles: true }));
      for (let n = 0; n < 120; n++) {
        await frame();
        if (doc.getElementById("day").textContent === "29") return;
      }
      throw Error("UI恢复超时");
    };
    for (let i = 0; i < 110; i++) {
      await restoreUI();
      const start = performance.now();
      doc.getElementById("step").click();
      await frame();
      assert(doc.getElementById("day").textContent === "30", "UI未推进到30日");
      if (i >= 10) ui.push(performance.now() - start);
    }
    for (const [samples, limit, name] of [
      [steps, 100, "单步"],
      [restores, 1000, "恢复"],
      [profiles, 500, "导入"],
      [ui, 500, "页面更新"],
    ])
      assert(summarize(samples, limit).pass, name + "P95超标");
    const details = doc.getElementById("agent-detail").textContent,
      world = a.world;
    out.textContent = JSON.stringify(
      {
        status: "PASS",
        environment: {
          userAgent: navigator.userAgent,
          platform: navigator.platform,
          hardwareConcurrency: navigator.hardwareConcurrency,
          viewport: [innerWidth, innerHeight],
          productViewport: [win.innerWidth, win.innerHeight],
        },
        method:
          "每项10次预热+100次样本；规则为29→30日；恢复使用31人day29全快照；人物导入恰好16KiB；UI样本包含命令、DOM更新及两次animation frame，保守覆盖渲染",
        step: summarize(steps, 100),
        restore: summarize(restores, 1000),
        profile: summarize(profiles, 500),
        ui: summarize(ui, 500),
        snapshotBytes: encoder.encode(a.exportSnapshot().data.json).length,
        uiChecks: {
          safeText: true,
          day30: true,
          population: doc.getElementById("population").textContent,
          proposalStatus: doc.getElementById("proposal-status").textContent,
          fullFileRestore: true,
        },
        uncaughtErrors: "See browser console check separately",
      },
      null,
      2,
    );
  } catch (error) {
    out.textContent = JSON.stringify({
      status: "FAIL",
      message: error.message,
    });
  } finally {
    button.disabled = false;
  }
};
