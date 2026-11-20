import { type Brush, box, ellipse, line } from "./brush";
import { castShadow, surface } from "./materials";
import type { Building } from "./buildings";
export function drawIndustry(c: Brush, b: Building): boolean {
  const { x, y, w, kind } = b;
  if (
    !["apiary", "loom", "furniture", "kitchen", "teahouse", "depot"].includes(
      kind,
    )
  )
    return false;
  if (kind === "loom") {
    for (const dx of [14, 76]) {
      castShadow(c, { x: x + dx, y: y + 20, w: 42, h: 55 }, 4);
      box(c, x + dx, y + 20, 42, 55, "#a68d65", 2);
      box(c, x + dx + 5, y + 24, 32, 44, "#f0dfb6", 1);
      for (let i = 0; i < 8; i++)
        line(
          c,
          [x + dx + 6 + i * 4, y + 23, x + dx + 6 + i * 4, y + 70],
          "#8ea9b5",
          1,
        );
      for (let i = 0; i < 6; i++)
        line(
          c,
          [x + dx + 5, y + 38 + i * 5, x + dx + 37, y + 38 + i * 5],
          "#b798a7",
          2,
        );
    }
  } else if (kind === "kitchen") {
    box(c, x + 12, y + 15, w - 24, 28, "#90a29d", 3);
    for (const dx of [30, 62, 94]) {
      ellipse(c, x + dx, y + 28, 12, 9, "#465c57");
      ellipse(c, x + dx, y + 26, 9, 6, "#dfb579");
      line(c, [x + dx - 15, y + 25, x + dx - 8, y + 25], "#d7dac1", 2);
    }
    castShadow(c, { x: x + 15, y: y + 61, w: w - 30, h: 24 }, 5);
    surface(
      c,
      { x: x + 15, y: y + 61, w: w - 30, h: 24 },
      "timber",
      "#c9b185",
      x,
    );
    for (let i = 0; i < 5; i++)
      ellipse(c, x + 28 + i * 19, y + 71, 6, 5, i % 2 ? "#8ca56b" : "#d9ac7c");
  } else if (kind === "teahouse") {
    for (const dx of [32, 101])
      for (const dy of [35, 76]) {
        ellipse(c, x + dx + 4, y + dy + 5, 22, 14, "#2e4a3c30");
        ellipse(c, x + dx, y + dy + 2, 21, 14, "#8f7149");
        const top = c.createLinearGradient(
          x + dx - 20,
          y + dy - 14,
          x + dx + 20,
          y + dy + 14,
        );
        top.addColorStop(0, "#d8b981");
        top.addColorStop(1, "#ac8454");
        ellipse(c, x + dx, y + dy, 21, 14, top);
        ellipse(c, x + dx, y + dy - 2, 5, 4, "#ede5c5");
        for (const side of [-1, 1])
          box(c, x + dx + side * 25 - 5, y + dy - 6, 10, 15, "#9fae8c", 2);
      }
  } else if (kind === "depot") {
    for (const dx of [12, 112])
      for (let row = 0; row < 3; row++) {
        box(c, x + dx + 3, y + 21 + row * 25, 48, 19, "#29453730", 2);
        surface(
          c,
          { x: x + dx, y: y + 18 + row * 25, w: 48, h: 19 },
          "timber",
          "#b99b6f",
          row + x,
        );
        line(
          c,
          [x + dx + 2, y + 20 + row * 25, x + dx + 46, y + 20 + row * 25],
          "#e5c691",
          1,
        );
        line(
          c,
          [x + dx + 4, y + 21 + row * 25, x + dx + 43, y + 33 + row * 25],
          "#e5cfa4",
          1,
        );
      }
    box(c, x + 67, y + 20, 32, 43, "#698f8d", 2);
    box(c, x + 70, y + 24, 26, 34, "#eee4c3", 1);
    for (let i = 0; i < 4; i++)
      line(c, [x + 73, y + 29 + i * 7, x + 93, y + 29 + i * 7], "#a4b196", 1);
  } else if (kind === "apiary") {
    for (const dx of [20, 54, 88]) {
      box(c, x + dx, y + 20, 22, 24, "#ad9463", 2);
      ellipse(c, x + dx + 11, y + 20, 11, 5, "#e2c277");
    }
    box(c, x + 16, y + 64, w - 32, 18, "#ccb282", 2);
    for (let i = 0; i < 7; i++) {
      box(c, x + 23 + i * 13, y + 62, 8, 12, "#68533044", 2);
      box(c, x + 22 + i * 13, y + 59, 8, 14, "#ce963b", 2);
      line(
        c,
        [x + 24 + i * 13, y + 62, x + 24 + i * 13, y + 69],
        "#ffe6a9aa",
        1.3,
      );
      box(c, x + 22 + i * 13, y + 57, 8, 3, "#f0dcab", 1);
    }
  } else {
    box(c, x + 14, y + 20, w - 28, 25, "#b58e5c", 3);
    line(c, [x + 24, y + 25, x + 53, y + 36], "#6b7a70", 3);
    for (const dx of [22, 62, 102]) {
      box(c, x + dx, y + 65, 22, 16, "#ba9a69", 2);
      box(c, x + dx, y + 53, 22, 8, "#cdb183", 2);
      line(c, [x + dx + 3, y + 58, x + dx + 3, y + 83], "#917750", 2);
    }
  }
  return true;
}
