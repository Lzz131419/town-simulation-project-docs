import { type Brush, box, ellipse, line, plant, seeded } from "./brush";
import { drawTree } from "./vegetation";
import { layout } from "../world-layout";
function clear(x: number, y: number) {
  return (
    !layout.buildings.some(
      (b) =>
        x > b.x - 24 &&
        x < b.x + b.w + 24 &&
        y > b.y - 25 &&
        y < b.y + b.h + 42,
    ) &&
    !layout.roads.some(
      (b) =>
        x > b.x - 24 &&
        x < b.x + b.w + 24 &&
        y > b.y - 10 &&
        y < b.y + b.h + 30,
    )
  );
}
function crate(c: Brush, x: number, y: number) {
  box(c, x, y, 18, 13, "#a68559", 2);
  box(c, x + 2, y + 1, 14, 9, "#d5b683", 1);
  line(c, [x + 2, y + 5, x + 16, y + 5], "#94774f", 1);
}
export function drawEastBank(c: Brush) {
  const random = seeded(781);
  // Forest floor and trees stay on land and leave entrances / paths clear.
  for (let i = 0; i < 30; i++)
    ellipse(
      c,
      1010 + random() * 380,
      30 + random() * 190,
      25 + random() * 30,
      13 + random() * 16,
      "#86ac7955",
    );
  for (let row = 0; row < 3; row++)
    for (let col = 0; col < 6; col++) {
      const x = 1000 + col * 46 + random() * 8,
        y = 26 + row * 52;
      if (clear(x, y)) drawTree(c, x, y, 0.75 + random() * 0.35, col % 3);
    }
  for (const [x, y] of [
    [1150, 190],
    [1190, 204],
    [1284, 232],
  ]) {
    box(c, x, y, 32, 10, "#876c4b", 4);
    ellipse(c, x + 3, y + 5, 4, 5, "#d4b889");
    line(c, [x + 10, y + 3, x + 26, y + 3], "#b59368", 1);
  }
  // Orchard rows, picking baskets and a packing bench.
  box(c, 1156, 252, 232, 126, "#92b87f", 12);
  for (let row = 0; row < 3; row++)
    for (let col = 0; col < 5; col++) {
      const x = 1180 + col * 43,
        y = 278 + row * 41;
      drawTree(c, x, y, 0.64, 1);
      for (const [dx, dy] of [
        [-6, -12],
        [7, -9],
        [1, -21],
      ])
        ellipse(
          c,
          x + dx,
          y + dy,
          2.5,
          2.5,
          (row + col) % 2 ? "#df9878" : "#e5bb70",
        );
    }
  crate(c, 1134, 341);
  crate(c, 1158, 348);
  // Rocky hill and rail siding, behind the single authoritative mine building.
  for (let i = 0; i < 14; i++) {
    const x = 1268 + (i % 4) * 31,
      y = 391 + Math.floor(i / 4) * 28;
    ellipse(c, x + 3, y + 6, 20, 11, "#68756322");
    ellipse(c, x, y, 19, 15, "#a4a394");
    ellipse(c, x - 5, y - 5, 12, 8, "#c9c6b2");
    line(c, [x - 9, y + 2, x, y - 4, x + 10, y + 1], "#8d9384", 1);
  }
  for (let y = 510; y < 550; y += 8) box(c, 1185, y, 39, 3, "#ab936e", 1);
  for (const x of [1193, 1216]) line(c, [x, 504, x, 550], "#6f807d", 2);
  box(c, 1246, 518, 30, 18, "#7a8b85", 3);
  ellipse(c, 1252, 538, 4, 4, "#46534c");
  ellipse(c, 1270, 538, 4, 4, "#46534c");
  for (let i = 0; i < 5; i++)
    ellipse(c, 1250 + i * 5, 517 - (i % 2) * 4, 4, 3, "#b5bbac");
  // Herb plots and drying rack alongside the greenhouse, not on its interior.
  for (let row = 0; row < 3; row++)
    for (let col = 0; col < 4; col++) {
      const x = 1214 + col * 30,
        y = 606 + row * 26;
      box(c, x, y, 24, 20, "#9d8963", 2);
      box(c, x + 2, y + 2, 20, 16, "#7a7551", 2);
      for (let i = 0; i < 3; i++) {
        ellipse(c, x + 6 + i * 6, y + 10, 4, 6, "#80a982");
        ellipse(c, x + 6 + i * 6, y + 6, 2, 2, row % 2 ? "#d6b2c5" : "#c9d99b");
      }
    }
  line(c, [1240, 693, 1240, 726, 1322, 726, 1322, 693], "#9c835e", 3);
  for (let i = 0; i < 7; i++) plant(c, 1249 + i * 10, 706, 0.4, true);
  // Riverside cooking station and fishing gear.
  box(c, 1060, 568, 36, 17, "#8c8a79", 3);
  box(c, 1064, 570, 28, 10, "#3e514b", 2);
  for (let i = 0; i < 5; i++)
    line(c, [1066 + i * 5, 572, 1066 + i * 5, 579], "#b0b6a0", 1);
  crate(c, 1000, 558);
  line(c, [974, 617, 969, 594, 954, 600], "#97794d", 1.8);
  line(c, [954, 600, 947, 614], "#e2dbbb", 0.6);
  ellipse(c, 947, 615, 1.5, 2, "#cd8b76");
  for (const [x, y] of [
    [1100, 219],
    [1137, 367],
    [1238, 568],
    [1087, 714],
  ])
    plant(c, x, y, 0.7, true);
}
export function drawSouthMeadow(c: Brush) {
  const r = seeded(654);
  // Patchwork cultivation with soil texture, seedlings and irrigation channels.
  for (let row = 0; row < 3; row++)
    for (let col = 0; col < 4; col++) {
      const x = 102 + col * 46,
        y = 758 + row * 53;
      box(c, x, y, 39, 43, "#a68b62", 3);
      for (let k = 0; k < 4; k++) {
        line(c, [x + 5, y + 7 + k * 9, x + 34, y + 7 + k * 9], "#826d4e", 1.5);
        for (let n = 0; n < 4; n++)
          ellipse(
            c,
            x + 7 + n * 7,
            y + 5 + k * 9,
            2,
            3,
            (row + col) % 2 ? "#a9bc77" : "#ccca87",
          );
      }
    }
  line(c, [88, 748, 88, 927, 291, 927], "#82b4a9", 5);
  // Camp lawn, picnic tables, tent and a cold fire circle.
  ellipse(c, 545, 824, 123, 73, "#b8cf9480");
  for (let i = 0; i < 45; i++) {
    const x = 390 + r() * 330,
      y = 735 + r() * 220;
    ellipse(c, x, y, 1.5, 1.5, i % 3 ? "#ead7a1" : "#d5a6b4");
  }
  for (const x of [465, 590]) {
    box(c, x, 805, 48, 19, "#b39a70", 3);
    box(c, x - 3, 800, 54, 5, "#d0b889", 2);
    box(c, x - 3, 826, 54, 5, "#bba074", 2);
    box(c, x + 13, 810, 13, 8, "#f4ebce", 1);
  }
  c.beginPath();
  c.moveTo(520, 798);
  c.lineTo(552, 755);
  c.lineTo(582, 798);
  c.closePath();
  c.fillStyle = "#c2b06c";
  c.fill();
  c.beginPath();
  c.moveTo(542, 798);
  c.lineTo(552, 773);
  c.lineTo(563, 798);
  c.closePath();
  c.fillStyle = "#687b60";
  c.fill();
  ellipse(c, 548, 892, 17, 11, "#87917a");
  ellipse(c, 548, 891, 12, 7, "#675e4d");
  line(c, [541, 888, 556, 895], "#ad9670", 3);
  line(c, [541, 895, 556, 887], "#927b59", 3);
  for (const [x, y] of [
    [390, 735],
    [430, 930],
    [670, 940],
  ])
    drawTree(c, x, y, 0.85, 1);
}
