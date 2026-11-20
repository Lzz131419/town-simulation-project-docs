import { contactShade } from "./materials";
import { drawShell } from "./building-shell";
import { drawIndustry } from "./industry";
import { layout } from "../world-layout";
import { type Brush, box, ellipse, line, plant } from "./brush";
export interface Building {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  kind:
    | "home"
    | "bakery"
    | "workshop"
    | "hall"
    | "shed"
    | "cabin"
    | "mine"
    | "greenhouse"
    | "fishery"
    | "apiary"
    | "loom"
    | "furniture"
    | "kitchen"
    | "teahouse"
    | "depot";
  tone: string;
}
export const BUILDINGS = layout.buildings as Building[];
function books(c: Brush, x: number, y: number, w: number) {
  box(c, x, y, w, 15, "#957657", 1);
  box(c, x + 2, y + 1, w - 4, 11, "#c6aa78", 1);
  const colors = ["#7c9f9b", "#bb8d73", "#b5ad71", "#7d8c9a", "#d4ba8b"];
  for (let i = 0; i < Math.floor((w - 6) / 5); i++) {
    box(c, x + 4 + i * 5, y + 3, 3, 8 + (i % 2), colors[i % 5], 0.5);
  }
  line(c, [x, y + 13, x + w, y + 13], "#e4d1a7", 1);
}
function table(c: Brush, x: number, y: number, w: number, h: number) {
  box(c, x + 2, y + 3, w, h, "#68775b22", 3);
  box(c, x, y, w, h, "#9c7b54", 3);
  box(c, x + 1, y, w - 2, h - 3, "#d7b987", 3);
  line(c, [x + 4, y + 3, x + w - 5, y + 3], "#f4d9a2", 1);
}
function bed(c: Brush, x: number, y: number, tone: string) {
  box(c, x + 2, y + 3, 27, 43, "#68775b22", 3);
  box(c, x, y, 27, 42, "#8d775e", 3);
  box(c, x + 2, y + 2, 23, 36, "#f3edd7", 3);
  box(c, x + 4, y + 3, 19, 9, "#fffcef", 3);
  box(c, x + 2, y + 16, 23, 23, tone, 2);
  line(c, [x + 5, y + 20, x + 22, y + 20], "#ffffff66", 1);
  box(c, x, y + 40, 27, 3, "#b3976b", 1);
}
function drawInterior(c: Brush, b: Building, index: number) {
  drawShell(c, b);
  if (drawIndustry(c, b)) return;
  const { x, y, w, h } = b;
  if (b.kind === "home") {
    bed(c, x + 12, y + 17, b.tone);
    books(c, x + 47, y + 12, w - 60);
    box(c, x + 45, y + 39, w - 61, 27, "#c9bc95", 3);
    box(c, x + 48, y + 42, w - 67, 21, b.tone, 3);
    line(c, [x + 51, y + 45, x + w - 24, y + 45], "#f2edce88", 1);
    table(c, x + w - 38, y + h - 31, 22, 17);
    box(c, x + w - 31, y + h - 28, 9, 7, "#f6e7bd", 1);
    ellipse(c, x + w - 21, y + h - 26, 2, 2, "#73958a");
    box(c, x + 43, y + 44, 6, 25, "#e4ebdd", 2);
    line(c, [x + 44, y + 51, x + 48, y + 51], "#99b5aa", 0.7);
    line(c, [x + 44, y + 61, x + 48, y + 61], "#99b5aa", 0.7);
    plant(c, x + w - 15, y + 33, 0.65);
    if (index % 2 === 0) {
      box(c, x + 12, y + h - 25, 19, 12, "#ad9876", 2);
      box(c, x + 14, y + h - 24, 15, 5, "#f2e6c5", 1);
    }
  } else if (b.kind === "bakery") {
    books(c, x + 12, y + 12, 68);
    books(c, x + w - 79, y + 12, 65);
    for (let i = 0; i < 3; i++) {
      box(c, x + 20 + i * 33, y + 38, 26, 23, "#7f8175", 3);
      box(c, x + 23 + i * 33, y + 42, 20, 12, "#424f4c", 2);
      ellipse(c, x + 33 + i * 33, y + 51, 6, 2, "#e4a15f");
      box(c, x + 23 + i * 33, y + 37, 20, 3, "#bbc0a7");
    }
    table(c, x + 17, y + h - 30, w - 34, 16);
    for (let i = 0; i < 7; i++) {
      ellipse(c, x + 30 + i * 23, y + h - 25, 7, 4, "#b58148");
      ellipse(c, x + 29 + i * 23, y + h - 26, 6, 3, "#e3b66b");
      line(
        c,
        [x + 27 + i * 23, y + h - 28, x + 29 + i * 23, y + h - 25],
        "#f9d99a",
        1,
      );
    }
    box(c, x + 151, y + 42, 29, 21, "#f5edce", 3);
    ellipse(c, x + 161, y + 51, 5, 4, "#d4ae6f");
    ellipse(c, x + 173, y + 50, 3, 3, "#dcd2b1");
    // Short awning at the entrance.
    for (let i = 0; i < 6; i++)
      box(
        c,
        x + w / 2 - 33 + i * 11,
        y + h - 3,
        11,
        10,
        i % 2 ? "#f8edda" : "#c68b7d",
        2,
      );
  } else if (b.kind === "workshop") {
    books(c, x + 12, y + 13, w - 24);
    table(c, x + 20, y + 42, w - 39, 24);
    line(c, [x + 31, y + 47, x + 46, y + 56], "#667367", 3);
    line(c, [x + 44, y + 44, x + 48, y + 51], "#a17a50", 2);
    box(c, x + w - 31, y + 37, 17, 11, "#9b7b52", 2);
    for (let i = 0; i < 3; i++)
      box(c, x + 14 + i * 21, y + h - 28, 18, 10, "#cfad76", 1);
    line(c, [x + 16, y + h - 24, x + 29, y + h - 24], "#8e714d", 1);
    plant(c, x + w - 17, y + h - 15, 0.6);
  } else if (b.kind === "cabin") {
    // Forest cabin: bed, fireplace, hunting trophies
    bed(c, x + 10, y + 15, b.tone);
    box(c, x + w - 35, y + 12, 22, 28, "#5a4a3a", 2);
    ellipse(c, x + w - 24, y + 26, 6, 8, "#e8a050");
    box(c, x + w - 30, y + 20, 4, 4, "#ff6a00");
    line(c, [x + 40, y + 15, x + 40, y + 30], "#8a7a5a", 2);
    ellipse(c, x + 40, y + 32, 4, 3, "#c8b89a");
    plant(c, x + w - 12, y + h - 12, 0.5);
  } else if (b.kind === "mine") {
    // Mine entrance: dark tunnel, support beams, ore carts
    box(c, x + 10, y + 10, w - 20, h - 20, "#3a3028", 2);
    box(c, x + 15, y + 15, w - 30, h - 30, "#1a1510", 1);
    // Support beams
    for (let i = 0; i < 3; i++) {
      box(c, x + 12 + i * 28, y + 8, 4, h - 16, "#6a5a4a", 1);
    }
    box(c, x + 8, y + 6, w - 16, 5, "#5a4a3a", 1);
    // Ore pile
    ellipse(c, x + w / 2, y + h - 8, 15, 6, "#4a3a2a");
    ellipse(c, x + w / 2 - 5, y + h - 12, 4, 3, "#8a7a6a");
    ellipse(c, x + w / 2 + 5, y + h - 10, 3, 2, "#7a6a5a");
  } else if (b.kind === "greenhouse") {
    // Greenhouse: glass panels, plant rows
    c.save();
    c.globalAlpha = 0.3;
    box(c, x + 5, y + 5, w - 10, h - 10, "#c8e8d8", 1);
    c.restore();
    for (let i = 0; i < 3; i++) {
      box(c, x + 10 + i * 25, y + 12, 20, h - 24, "#a8c898", 1);
      for (let j = 0; j < 3; j++) {
        ellipse(c, x + 20 + i * 25, y + 20 + j * 15, 4, 3, "#6a9a5a");
        ellipse(c, x + 20 + i * 25, y + 20 + j * 15, 2, 1, "#8aba7a");
      }
    }
  } else if (b.kind === "fishery") {
    // Fishery hut: nets, crates, fishing rods
    box(c, x + 5, y + 5, w - 10, h - 10, "#d8c8a8", 1);
    // Nets
    for (let i = 0; i < 3; i++) {
      line(
        c,
        [x + 10, y + 10 + i * 8, x + w - 10, y + 10 + i * 8],
        "#8a9aaa",
        0.5,
      );
    }
    for (let i = 0; i < 4; i++) {
      line(
        c,
        [x + 12 + i * 12, y + 8, x + 12 + i * 12, y + h - 8],
        "#8a9aaa",
        0.5,
      );
    }
    // Crates
    box(c, x + 8, y + h - 18, 14, 12, "#9a8a6a", 1);
    box(c, x + 24, y + h - 15, 10, 9, "#8a7a5a", 1);
    // Fishing rod
    line(c, [x + w - 15, y + 8, x + w - 5, y + h - 5], "#7a6a4a", 2);
    line(c, [x + w - 5, y + h - 5, x + w - 2, y + h - 2], "#aaa", 0.5);
  } else if (b.kind === "hall") {
    box(c, x + 12, y + 14, 34, 23, "#a08861", 2);
    box(c, x + 14, y + 16, 30, 19, "#e6e0bc", 1);
    box(c, x + 18, y + 20, 9, 7, "#9eaf83", 1);
    box(c, x + 30, y + 19, 10, 11, "#c4ab80", 1);
    table(c, x + 51, y + 18, 45, 23);
    box(c, x + 60, y + 21, 19, 13, "#f5efd9", 1);
    line(c, [x + 63, y + 25, x + 75, y + 25], "#91a89a", 1);
    for (let i = 0; i < 3; i++) {
      box(c, x + 18 + i * 28, y + h - 26, 15, 12, "#8da69b", 3);
      box(c, x + 18 + i * 28, y + h - 28, 15, 4, "#b8c7ad", 2);
    }
  } else {
    books(c, x + 13, y + 12, 57);
    table(c, x + w - 47, y + 15, 30, 21);
    for (let i = 0; i < 4; i++) {
      box(c, x + 14 + i * 22, y + h - 24, 17, 13, "#ad8e5d", 2);
      ellipse(c, x + 22 + i * 22, y + h - 21, 6, 3, "#ccbf76");
    }
  }
}
export function drawBuilding(c: Brush, b: Building, index: number) {
  drawInterior(c, b, index);
  const { x, y, w, h } = b;
  // Window light lands on the floor; subtle edge shading connects furniture to the room.
  c.save();
  c.beginPath();
  c.rect(x + 5, y + 8, w - 10, h - 13);
  c.clip();
  const beam = c.createLinearGradient(x + 12, y + 12, x + w * 0.65, y + h);
  beam.addColorStop(0, "#fff3b526");
  beam.addColorStop(1, "#fff3b500");
  c.fillStyle = beam;
  c.beginPath();
  c.moveTo(x + 15, y + 8);
  c.lineTo(x + 38, y + 8);
  c.lineTo(x + 75, y + h - 10);
  c.lineTo(x + 29, y + h - 10);
  c.fill();
  c.restore();
  contactShade(c, { x: x + 5, y: y + 8, w: w - 10, h: h - 13 }, 8);
  if (b.kind === "greenhouse") {
    c.save();
    c.beginPath();
    c.rect(x + 6, y + 9, w - 12, h - 16);
    c.clip();
    for (let xx = x + 8; xx < x + w; xx += 28) {
      line(c, [xx, y + 10, xx, y + h - 8], "#476f6855", 1.5);
      c.fillStyle = "#e0f8ee30";
      c.beginPath();
      c.moveTo(xx + 2, y + 10);
      c.lineTo(xx + 9, y + 10);
      c.lineTo(xx + 24, y + h - 9);
      c.lineTo(xx + 16, y + h - 9);
      c.fill();
    }
    line(c, [x + 6, y + h * 0.55, x + w - 6, y + h * 0.55], "#d0e6d0aa", 1);
    c.restore();
  }
  // Threshold and right-facing wall have thickness, with a clean sunlit cap.
  box(c, x + w - 4, y + 9, 4, h - 10, "#465d5150");
  line(c, [x + 1, y + 10, x + 1, y + h - 6], "#f7f3d5aa", 1);
}
export function drawPlaza(c: Brush) {
  box(c, 381, 336, 245, 130, "#7f9f77", 7);
  box(c, 388, 342, 231, 118, "#d2d3b9", 4);
  for (let y = 345; y < 458; y += 14)
    for (let x = 391; x < 616; x += 19)
      box(c, x, y, 17, 12, (x + y) % 4 ? "#ece9d2" : "#dce0cb", 1);
  // Fountain is also a server collision rectangle: 481,371,63,52.
  ellipse(c, 517, 403, 38, 24, "#697d6c33");
  ellipse(c, 512, 397, 31, 23, "#b3b7a0");
  ellipse(c, 512, 393, 31, 21, "#f5ecd3");
  ellipse(c, 512, 393, 26, 16, "#68b1b5");
  ellipse(c, 512, 391, 23, 13, "#96cccb");
  box(c, 508, 374, 9, 22, "#d9ddca", 3);
  ellipse(c, 512, 374, 12, 5, "#f5edcf");
  ellipse(c, 512, 372, 10, 3, "#a5c9bc");
  for (const [x, y] of [
    [407, 353],
    [566, 353],
    [408, 437],
    [566, 437],
  ]) {
    box(c, x + 3, y + 4, 30, 12, "#7d80602b", 2);
    box(c, x, y, 30, 5, "#a38255", 1);
    box(c, x, y + 7, 30, 5, "#bfa175", 1);
    box(c, x + 3, y + 10, 3, 7, "#7d7354");
    box(c, x + 24, y + 10, 3, 7, "#7d7354");
  }
  for (let i = 0; i < 8; i++) {
    plant(c, 399 + i * 30, 331, 0.5, true);
    plant(c, 399 + i * 30, 467, 0.5, true);
  }
  // Market stalls share the square's northern edge.
  for (const x of [425, 558]) {
    table(c, x, 319, 32, 13);
    for (let i = 0; i < 4; i++) {
      box(c, x + i * 8, 310, 8, 13, i % 2 ? "#f6edcf" : "#a5bab0", 2);
    }
    ellipse(c, x + 9, 323, 4, 2, "#d6ac65");
  }
}
