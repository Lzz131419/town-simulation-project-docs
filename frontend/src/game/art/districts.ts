import { surface, type Material } from "./materials";
import { type Brush, box, ellipse, line, plant } from "./brush";
import { layout } from "../world-layout";

export function drawDistrictGround(c: Brush) {
  for (const p of layout.parcels) {
    const material: Material = /garden|flax|apiary|camp/.test(p.id)
      ? "earth"
      : /kitchen|tea|craft-square/.test(p.id)
        ? "brick"
        : "stone";
    const base =
      material === "earth"
        ? "#b8b183"
        : material === "brick"
          ? "#c2a88d"
          : "#c5c3ad";
    box(c, p.x - 4, p.y - 4, p.w + 8, p.h + 8, "#85966d", 6);
    box(c, p.x - 2, p.y - 2, p.w + 4, p.h + 4, "#ded3b7", 4);
    surface(c, p, material, base, p.x + p.y);
  }
}
function bench(c: Brush, x: number, y: number) {
  box(c, x, y, 42, 8, "#9b805e", 2);
  box(c, x, y + 10, 42, 6, "#c7ab7b", 2);
  for (const dx of [5, 32]) box(c, x + dx, y + 14, 4, 7, "#6e795f", 1);
}
function crate(c: Brush, x: number, y: number, color = "#c3a67b") {
  box(c, x + 3, y + 3, 24, 20, "#59674a22", 2);
  box(c, x, y, 24, 18, color, 2);
  line(
    c,
    [x + 3, y + 3, x + 21, y + 15, x + 21, y + 3, x + 3, y + 15],
    "#8e7757",
    1,
  );
}
export function drawDistrictDetails(c: Brush) {
  // Flower beds and actual hives are concentrated around the new bee yard.
  for (let row = 0; row < 3; row++)
    for (let col = 0; col < 5; col++) {
      const x = 1584 + col * 35,
        y = 84 + row * 46;
      box(c, x, y, 27, 32, "#a5b679", 4);
      for (let k = 0; k < 5; k++)
        ellipse(
          c,
          x + 5 + (k % 3) * 7,
          y + 7 + Math.floor(k / 3) * 12,
          3,
          3,
          col % 2 ? "#ead59a" : "#c7a7c8",
        );
    }
  for (const x of [1560, 1620, 1680]) {
    box(c, x, 216, 28, 19, "#cfaf6b", 2);
    box(c, x - 3, 211, 34, 5, "#f1db9e", 2);
    for (let y = 221; y < 232; y += 5)
      line(c, [x + 2, y, x + 26, y], "#9e804b", 1);
  }
  // Blue flax plots and a drying rail beside the shed.
  for (let row = 0; row < 4; row++)
    for (let col = 0; col < 6; col++) {
      const x = 1640 + col * 24,
        y = 294 + row * 37;
      box(c, x, y, 20, 30, "#8a8e62", 2);
      for (let k = 0; k < 3; k++) {
        line(c, [x + 4 + k * 6, y + 24, x + 4 + k * 6, y + 8], "#9ebc84", 1);
        ellipse(c, x + 4 + k * 6, y + 8, 2.5, 3, "#aac5de");
      }
    }
  for (const x of [1440, 1480, 1520]) {
    box(c, x, 704, 28, 16, "#d8d0b2", 2);
    line(c, [x + 2, 709, x + 26, 709], "#8caeb0", 3);
    line(c, [x + 2, 716, x + 26, 716], "#c5a2a9", 2);
  }
  for (const x of [1650, 1700, 1750]) {
    box(c, x, 703, 35, 16, "#b99461", 2);
    box(c, x + 3, 717, 4, 8, "#7d785b");
    box(c, x + 27, 717, 4, 8, "#7d785b");
  }
  // Paved squares have stalls and seating, rather than solid belts of trees.
  for (const [x, y] of [
    [395, 1020],
    [530, 1020],
    [665, 1020],
    [1450, 784],
    [1630, 784],
  ]) {
    box(c, x, y, 70, 22, "#a88b63", 3);
    for (let i = 0; i < 7; i++)
      box(c, x + i * 10, y - 12, 10, 19, i % 2 ? "#f4e4c5" : "#b29a91", 2);
    for (let i = 0; i < 4; i++)
      ellipse(c, x + 12 + i * 14, y + 13, 5, 3, i % 2 ? "#d8bd79" : "#91a681");
  }
  for (const [x, y] of [
    [410, 1100],
    [690, 1100],
    [1070, 1140],
    [1200, 1140],
    [1220, 906],
    [1220, 956],
  ])
    bench(c, x, y);
  for (const x of [700, 750, 800]) crate(c, x, 898, "#b6bc8a");
  // Freight court: loading bays, packed goods and a cart.
  for (const x of [1392, 1650, 1730])
    for (let row = 0; row < 3; row++) crate(c, x, 1130 + row * 25);
  line(c, [1410, 1108, 1610, 1108], "#f4ebce", 3);
  for (let x = 1440; x < 1600; x += 46)
    line(c, [x, 1110, x, 1200], "#f4ebce", 2);
  box(c, 1660, 918, 96, 34, "#7f9e9f", 3);
  box(c, 1726, 908, 30, 44, "#93afb1", 4);
  box(c, 1732, 913, 18, 15, "#d1e3d7", 2);
  for (const x of [1678, 1743]) ellipse(c, x, 955, 8, 8, "#53685e");
  // A moored boat sits in the river; walking still requires a bridge.
  ellipse(c, 937, 1160, 17, 47, "#628e89");
  ellipse(c, 935, 1156, 14, 43, "#a58a63");
  box(c, 924, 1130, 22, 49, "#d8c297", 5);
  line(c, [948, 1150, 976, 1144], "#a99970", 1.5);
  for (const [x, y] of [
    [404, 1180],
    [820, 1180],
    [1260, 1200],
    [1750, 1180],
    [1380, 784],
  ])
    plant(c, x, y, 1, true);
}
