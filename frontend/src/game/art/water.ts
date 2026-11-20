import { type Brush, box, ellipse, line, seeded } from "./brush";
import { surface } from "./materials";
import { layout } from "../world-layout";
export function drawRiver(c: Brush) {
  const { river: r, bounds: b } = layout,
    random = seeded(84);
  box(c, r.x - 11, b.y, r.width + 22, b.height, "#839e75");
  box(c, r.x - 7, b.y, r.width + 14, b.height, "#c6b997");
  const depth = c.createLinearGradient(r.x, 0, r.x + r.width, 0);
  for (const [p, tone] of [
    [0, "#81b8a6"],
    [0.15, "#569d96"],
    [0.65, "#347d87"],
    [0.9, "#438f93"],
    [1, "#70aaa0"],
  ] as const)
    depth.addColorStop(p, tone);
  c.fillStyle = depth;
  c.fillRect(r.x, b.y, r.width, b.height);
  // Submerged stones and meandering current highlights, clipped to the water.
  c.save();
  c.beginPath();
  c.rect(r.x, b.y, r.width, b.height);
  c.clip();
  for (let i = 0; i < 170; i++) {
    const side = i % 2,
      x = r.x + (side ? r.width - 4 : 4) + random() * 5 - 2,
      y = b.y + random() * b.height;
    ellipse(c, x, y, 1 + random() * 3, 2 + random() * 4, "#d2d6ac26");
  }
  for (let y = b.y; y < b.y + b.height; y += 24) {
    const x = r.x + 10 + Math.sin(y / 90) * 6;
    line(c, [x, y, x + 5, y + 10, x + 3, y + 19], "#b0d9c825", 1.8);
    const xx = r.x + 24 + random() * 10;
    line(c, [xx, y + 8, xx + 9, y + 7, xx + 12, y + 8], "#d8ede552", 0.7);
  }
  // Soft reflections under the bank, leaving the deep channel visible.
  const shade = c.createLinearGradient(r.x, 0, r.x + 14, 0);
  shade.addColorStop(0, "#294f4445");
  shade.addColorStop(1, "#294f4400");
  c.fillStyle = shade;
  c.fillRect(r.x, b.y, 14, b.height);
  c.restore();
  for (let y = b.y; y < b.y + b.height; y += 18) {
    for (const x of [r.x - 7, r.x + r.width + 1]) {
      box(c, x, y, 6, 16, random() > 0.5 ? "#a7ac8c" : "#bebd9e", 1);
      line(c, [x, y, x + 5, y], "#e3dbb8", 0.8);
    }
  }
  for (let y = b.y + 20; y < b.y + b.height; y += 43) {
    for (const x of [r.x - 10, r.x + r.width + 9]) {
      ellipse(c, x, y + 5, 4, 2, "#4f77534a");
      line(c, [x - 3, y, x, y - 7, x + 2, y - 1], "#50825f", 1.1);
    }
  }
}
export function drawBridges(c: Brush) {
  for (const b of layout.bridges) {
    box(c, b.x + 5, b.y + 9, b.w, b.h, "#234f5944", 3);
    box(c, b.x, b.y, b.w, b.h, "#725336", 2);
    surface(
      c,
      { x: b.x + 2, y: b.y + 2, w: b.w - 4, h: b.h - 4 },
      "timber",
      "#b89964",
      b.y,
    );
    // Crosswise joists and bolt heads make the bridge read as timber.
    for (let x = b.x + 3; x < b.x + b.w - 2; x += 8) {
      line(c, [x, b.y + 2, x, b.y + b.h - 2], "#78533299", 0.8);
      for (const y of [b.y + 5, b.y + b.h - 5])
        ellipse(c, x + 3, y, 0.7, 0.7, "#5a6154");
    }
    for (const y of [b.y - 2, b.y + b.h - 2]) {
      box(c, b.x - 2, y + 3, b.w + 4, 4, "#31594e33", 1);
      box(c, b.x - 2, y, b.w + 4, 4, "#876543", 1);
      line(c, [b.x - 2, y, b.x + b.w + 2, y], "#e4c58b", 1);
      for (const x of [b.x, b.x + b.w / 2, b.x + b.w]) {
        box(c, x - 2, y - 7, 5, 12, "#6e5439", 1);
        box(c, x - 2, y - 8, 5, 2, "#d1b17b", 1);
      }
    }
  }
}
