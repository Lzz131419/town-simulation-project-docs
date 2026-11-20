import { surface } from "./materials";
import { type Brush, box, ellipse, line, palette, seeded } from "./brush";
import { layout } from "../world-layout";
import { drawTree } from "./vegetation";
import { drawRiver, drawBridges } from "./water";
import { drawEastBank, drawSouthMeadow } from "./regions";
import { drawDistrictGround, drawDistrictDetails } from "./districts";
export { TREES, drawTree } from "./vegetation";
export const SCENE_BOUNDS = layout.bounds;
export function drawTerrain(c: Brush) {
  const b = SCENE_BOUNDS,
    r = seeded(2491);
  box(c, b.x, b.y, b.width, b.height, palette.grass);
  // Low frequency color variation makes meadow light and moisture visible.
  for (let i = 0; i < 150; i++) {
    const x = b.x + r() * b.width,
      y = b.y + r() * b.height,
      radius = 40 + r() * 120;
    const glow = c.createRadialGradient(x, y, 0, x, y, radius);
    glow.addColorStop(0, i % 3 ? "#d4df8d20" : "#2e6e4930");
    glow.addColorStop(1, i % 3 ? "#d4df8d00" : "#2e6e4900");
    ellipse(c, x, y, radius, radius, glow);
  }
  for (let i = 0; i < 13000; i++) {
    const x = b.x + r() * b.width,
      y = b.y + r() * b.height;
    c.globalAlpha = 0.15 + r() * 0.2;
    line(
      c,
      [x, y, x + 1, y - 2, x + 2.5, y],
      r() > 0.6 ? "#568a61" : "#d1e3a9",
      0.65,
    );
  }
  c.globalAlpha = 1;
  drawDistrictGround(c);
  drawRiver(c);
  for (const p of layout.roads) {
    box(c, p.x - 3, p.y - 3, p.w + 6, p.h + 6, palette.pathEdge, 5);
    surface(c, p, "earth", palette.path, p.x * 3 + p.y);
    for (let i = 0; i < (p.w * p.h) / 110; i++)
      ellipse(c, p.x + r() * p.w, p.y + r() * p.h, 0.65, 0.4, "#bcae8950");
  }
  drawBridges(c);
  drawEastBank(c);
  drawSouthMeadow(c);
  drawDistrictDetails(c);
  for (let i = 0; i < 24; i++) {
    const x = b.x + r() * b.width,
      y = b.y + r() * b.height;
    if ((x < 20 || y < -25 || y > 1290) && (x < 890 || x > 990))
      drawTree(c, x, y, 0.75 + r() * 0.4, i % 3);
  }
}
export function drawField(c: Brush) {
  box(c, 74, 325, 190, 86, "#b99169", 4);
  for (let row = 0; row < 4; row++)
    for (let col = 0; col < 8; col++) {
      const x = 81 + col * 23,
        y = 330 + row * 20;
      box(c, x, y, 19, 15, "#8e7051", 2);
      line(c, [x + 1, y + 13, x + 17, y + 13], "#a8855c", 1);
      line(c, [x + 9, y + 12, x + 9, y - 1], "#6b8c50", 1.5);
      for (let k = 0; k < 3; k++) {
        const yy = y + 1 + k * 3;
        ellipse(c, x + 6, yy, 3, 1.5, "#c9bf6b");
        ellipse(c, x + 12, yy - 1, 3, 1.5, "#e1d28a");
      }
    }
  for (let x = 70; x <= 267; x += 22) {
    box(c, x, 315, 4, 15, "#9a8058", 1);
    box(c, x, 407, 4, 14, "#9a8058", 1);
  }
  for (const y of [318, 324, 410, 416]) {
    box(c, 70, y, 199, 2, "#d3bd8a", 1);
  }
  // Watering can and stacked harvest baskets.
  ellipse(c, 279, 393, 8, 4, "#789992");
  box(c, 272, 383, 13, 11, "#8bada1", 3);
  line(c, [284, 388, 291, 382], "#678980", 2);
  box(c, 72, 435, 19, 12, "#bc9564", 3);
  box(c, 74, 432, 15, 7, "#d3bc83", 3);
}
