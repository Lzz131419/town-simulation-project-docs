import { drawLamps } from "./lighting-props";
import { box, plant } from "./brush";
import {
  drawTerrain,
  drawField,
  drawTree,
  TREES,
  SCENE_BOUNDS,
} from "./terrain";
import { BUILDINGS, drawBuilding, drawPlaza } from "./buildings";
export { BUILDINGS, SCENE_BOUNDS };
export function makeMapTexture(scale = 3) {
  const canvas = document.createElement("canvas");
  canvas.width = SCENE_BOUNDS.width * scale;
  canvas.height = SCENE_BOUNDS.height * scale;
  const c = canvas.getContext("2d")!;
  c.scale(scale, scale);
  c.translate(-SCENE_BOUNDS.x, -SCENE_BOUNDS.y);
  drawTerrain(c);
  drawField(c);
  drawPlaza(c);
  BUILDINGS.forEach((b, i) => drawBuilding(c, b, i));
  TREES.forEach(([x, y, s], i) => drawTree(c, x, y, s, i % 4 === 0 ? 1 : 0));
  // Decorative plants
  for (const [x, y] of [
    [351, 470],
    [704, 471],
    [279, 176],
    [633, 176],
    [875, 418],
    [62, 291],
  ])
    plant(c, x, y, 0.9, true);
  // North-bank decorations
  for (const [x, y] of [
    [980, 320],
    [1120, 180],
    [1080, 480],
    [1180, 580],
    [960, 580],
    [1020, 680],
  ])
    plant(c, x, y, 0.7, true);
  // Notice board next to the community office.
  box(c, 865, 402, 3, 28, "#8b7457", 1);
  box(c, 855, 393, 24, 23, "#a78b5f", 2);
  box(c, 858, 396, 18, 16, "#eee2bd", 1);
  box(c, 861, 399, 5, 7, "#a3b6a0", 1);
  box(c, 868, 398, 5, 10, "#d0b17f", 1);
  drawLamps(c);
  return canvas;
}
