import { type Brush, box, ellipse, line, seeded } from "./brush";

export interface Surface {
  x: number;
  y: number;
  w: number;
  h: number;
}
export type Material = "stone" | "brick" | "timber" | "earth";
// Static, deterministic material detail is baked once into the map texture.
export function surface(
  c: Brush,
  p: Surface,
  material: Material,
  base: string,
  seed = 1,
) {
  const r = seeded(seed);
  c.save();
  c.beginPath();
  c.roundRect(p.x, p.y, p.w, p.h, 3);
  c.clip();
  box(c, p.x, p.y, p.w, p.h, base);
  const wash = c.createLinearGradient(p.x, p.y, p.x + p.w * 0.4, p.y + p.h);
  wash.addColorStop(0, "#fff4cc20");
  wash.addColorStop(1, "#3e514117");
  c.fillStyle = wash;
  c.fillRect(p.x, p.y, p.w, p.h);
  if (material === "earth") {
    for (let i = 0; i < (p.w * p.h) / 90; i++) {
      const x = p.x + r() * p.w,
        y = p.y + r() * p.h;
      ellipse(
        c,
        x,
        y,
        0.4 + r() * 1.2,
        0.3 + r() * 0.6,
        i % 3 ? "#805c3529" : "#fff2cc66",
      );
    }
  } else {
    const tw = material === "brick" ? 20 : material === "timber" ? 48 : 27;
    const th = material === "brick" ? 10 : material === "timber" ? 10 : 20;
    let row = 0;
    for (let y = p.y; y < p.y + p.h; y += th, row++) {
      for (let x = p.x - ((row % 2) * tw) / 2; x < p.x + p.w; x += tw) {
        box(
          c,
          x + 1,
          y + 1,
          tw - 2,
          th - 2,
          r() > 0.5 ? "#fff4df16" : "#354d3b0c",
          1,
        );
        line(c, [x, y + th, x + tw, y + th], "#5b59422e", 0.7);
        line(c, [x, y, x, y + th], "#5b59422e", 0.7);
        line(c, [x + 1, y + 1, x + tw - 1, y + 1], "#fff7df42", 0.7);
        if (material === "timber") {
          line(
            c,
            [x + 4, y + 4, x + tw - 7, y + 4 + r() * 2],
            "#6d4b2829",
            0.6,
          );
          if (r() > 0.8) ellipse(c, x + tw * 0.6, y + 5, 3, 0.8, "#6d4b2829");
        } else if (r() > 0.86) {
          line(
            c,
            [x + tw - 5, y + 2, x + tw - 8, y + 6, x + tw - 6, y + 9],
            "#64694b25",
            0.6,
          );
        }
      }
    }
  }
  c.restore();
}

export function contactShade(c: Brush, p: Surface, depth = 12) {
  c.save();
  c.beginPath();
  c.rect(p.x, p.y, p.w, p.h);
  c.clip();
  const top = c.createLinearGradient(0, p.y, 0, p.y + depth);
  top.addColorStop(0, "#293f364d");
  top.addColorStop(1, "#293f3600");
  c.fillStyle = top;
  c.fillRect(p.x, p.y, p.w, depth);
  const side = c.createLinearGradient(p.x + p.w - depth, 0, p.x + p.w, 0);
  side.addColorStop(0, "#293f3600");
  side.addColorStop(1, "#293f3633");
  c.fillStyle = side;
  c.fillRect(p.x + p.w - depth, p.y, depth, p.h);
  c.restore();
}

export function castShadow(c: Brush, p: Surface, height = 14) {
  c.save();
  // Sun from upper left. Broad penumbra sits outside a tighter contact shadow.
  for (const [offset, alpha] of [
    [3, 0.035],
    [1.5, 0.05],
    [0, 0.12],
  ]) {
    c.beginPath();
    c.moveTo(p.x - offset, p.y + p.h - 2);
    c.lineTo(p.x + p.w, p.y - 2);
    c.lineTo(p.x + p.w + height + offset, p.y + height * 0.8);
    c.lineTo(p.x + p.w + height + offset, p.y + p.h + height * 0.8 + offset);
    c.lineTo(p.x + height, p.y + p.h + height * 0.8 + offset);
    c.closePath();
    c.fillStyle = `rgba(32,59,48,${alpha})`;
    c.fill();
  }
  box(c, p.x + 2, p.y + p.h - 2, p.w, 6, "#203b4826", 2);
  c.restore();
}
