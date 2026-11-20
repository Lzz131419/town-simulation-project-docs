import { type Brush, box, ellipse, line, seeded } from "./brush";
export const TREES: [number, number, number][] = [
  [36, 80, 1.1],
  [87, 64, 1.05],
  [124, 96, 0.9],
  [38, 141, 0.9],
  [83, 154, 1.1],
  [30, 207, 0.8],
  [879, 72, 1],
  [892, 126, 0.8],
  [879, 205, 1],
  [878, 259, 0.9],
  [871, 475, 1],
  [883, 576, 1],
  [38, 467, 1.1],
  [85, 494, 0.8],
  [35, 551, 1],
  [90, 590, 1],
  [38, 633, 1],
  [111, 651, 0.8],
  [362, 213, 0.8],
  [362, 260, 0.85],
  [713, 215, 0.8],
  [711, 565, 0.9],
  [709, 609, 0.9],
  ...Array.from({ length: 7 }, (_, i): [number, number, number] => [
    159 + i * 106,
    18,
    0.76,
  ]),
  ...Array.from({ length: 7 }, (_, i): [number, number, number] => [
    165 + i * 102,
    653,
    0.75,
  ]),
];
export function drawTree(c: Brush, x: number, y: number, s = 1, variant = 0) {
  c.save();
  c.translate(x, y);
  c.scale(s, s);
  const r = seeded(Math.round(x * 13 + y * 7 + variant * 31));
  ellipse(c, 17, 22, 30, 10, "#244c3820");
  ellipse(c, 11, 18, 24, 8, "#244c3828");
  ellipse(c, 2, 19, 9, 3, "#244c3840");
  box(c, -3, -8, 8, 30, "#795936", 2);
  line(c, [-1, 18, -1, -9, -10, -17], "#bf9a61", 1.5);
  line(c, [3, 10, 8, -6, 15, -15], "#674b32", 2);
  const colors = variant
    ? ["#a8bd63", "#74994e", "#426c49"]
    : ["#93bb66", "#54894e", "#305f49"];
  const canopy = c.createLinearGradient(-20, -45, 22, 8);
  canopy.addColorStop(0, colors[0]);
  canopy.addColorStop(0.45, colors[1]);
  canopy.addColorStop(1, colors[2]);
  c.beginPath();
  for (let i = 0; i <= 36; i++) {
    const angle = (i / 36) * Math.PI * 2,
      radius = 27 + Math.sin(i * 2.4) * 2 + r() * 3;
    const px = Math.cos(angle) * radius,
      py = -18 + Math.sin(angle) * radius * 0.9;
    if (i === 0) c.moveTo(px, py);
    else c.lineTo(px, py);
  }
  c.closePath();
  c.fillStyle = canopy;
  c.fill();
  c.save();
  c.clip();
  // Smaller overlapping leaf clusters replace the four glossy canopy spheres.
  for (let i = 0; i < 65; i++) {
    const px = -28 + r() * 56,
      py = -46 + r() * 52,
      size = 2 + r() * 5;
    const light = (px + py + 50) / 85;
    ellipse(c, px + 1, py + 2, size, size * 0.6, "#294b3922");
    ellipse(
      c,
      px,
      py,
      size,
      size * 0.65,
      light < 0.4 ? "#c3d7854a" : light > 0.7 ? "#234e3d2b" : "#88b46244",
    );
    if (i % 4 === 0) line(c, [px - 2, py, px + 1, py - 1], "#dfdf9c50", 0.8);
  }
  c.restore();
  c.restore();
}
