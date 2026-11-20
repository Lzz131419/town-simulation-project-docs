import { type Brush, box, ellipse, line } from "./brush";
export const LAMP_POSTS: [number, number][] = [
  [382, 341],
  [626, 341],
  [382, 463],
  [626, 463],
  [1388, 264],
  [1392, 738],
  [1800, 738],
  [1300, 1020],
  [1390, 1090],
  [1720, 1090],
  [390, 1180],
  [850, 1180],
];
export function drawLamps(c: Brush) {
  for (const [x, y] of LAMP_POSTS) {
    line(c, [x, y, x + 17, y + 8], "#294c3b33", 3);
    ellipse(c, x, y + 1, 5, 2, "#405e4c55");
    box(c, x - 1, y - 25, 3, 26, "#4b6256", 1);
    line(c, [x - 1, y - 23, x - 1, y - 1], "#bac3a0", 0.6);
    box(c, x - 5, y - 31, 11, 9, "#44584c", 2);
    box(c, x - 3, y - 29, 7, 5, "#f5d18a", 1);
    line(c, [x - 5, y - 31, x + 6, y - 31], "#b5bb93", 1);
    box(c, x, y - 30, 1, 7, "#6e7050");
  }
}
