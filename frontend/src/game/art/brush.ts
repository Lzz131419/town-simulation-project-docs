export type Brush = CanvasRenderingContext2D;
export const palette = {
  grass: "#91b979",
  grassLight: "#b0ca86",
  grassDark: "#588764",
  path: "#ddc69d",
  pathEdge: "#9aab79",
  ink: "#526454",
  water: "#4a9f9f",
  waterDark: "#52949f",
  wall: "#f8f1da",
};
export function box(
  c: Brush,
  x: number,
  y: number,
  w: number,
  h: number,
  fill: string,
  radius = 0,
  stroke?: string,
) {
  c.beginPath();
  c.roundRect(x, y, w, h, radius);
  c.fillStyle = fill;
  c.fill();
  if (stroke) {
    c.strokeStyle = stroke;
    c.lineWidth = 1;
    c.stroke();
  }
}
export function ellipse(
  c: Brush,
  x: number,
  y: number,
  rx: number,
  ry: number,
  fill: string | CanvasGradient,
) {
  c.beginPath();
  c.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
  c.fillStyle = fill;
  c.fill();
}
export function line(c: Brush, points: number[], color: string, width = 1) {
  c.beginPath();
  c.moveTo(points[0], points[1]);
  for (let i = 2; i < points.length; i += 2) c.lineTo(points[i], points[i + 1]);
  c.strokeStyle = color;
  c.lineWidth = width;
  c.lineCap = "round";
  c.lineJoin = "round";
  c.stroke();
}
export function seeded(seed: number) {
  let n = seed;
  return () => {
    n = (n * 1664525 + 1013904223) >>> 0;
    return n / 4294967296;
  };
}
export function plant(
  c: Brush,
  x: number,
  y: number,
  size = 1,
  flower = false,
) {
  c.save();
  c.translate(x, y);
  c.scale(size, size);
  box(c, -6, 0, 12, 9, "#ba8662", 2);
  box(c, -7, -1, 14, 3, "#d3a679", 1);
  ellipse(c, -3, -5, 5, 6, "#628c61");
  ellipse(c, 3, -7, 5, 7, "#79a36b");
  if (flower) {
    for (const [px, py] of [
      [-4, -9],
      [3, -13],
      [5, -6],
    ]) {
      ellipse(c, px, py, 3, 3, "#e3a69b");
      ellipse(c, px, py, 1, 1, "#fff1bd");
    }
  }
  c.restore();
}
