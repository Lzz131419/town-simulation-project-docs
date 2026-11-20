import { type Brush, box, line } from "./brush";
import { surface, contactShade, castShadow } from "./materials";
import type { Building } from "./buildings";
function buildingShadow(c: Brush, b: Building) {
  castShadow(c, b, b.kind === "home" ? 15 : 20);
}

function drawRoof(c: Brush, b: Building) {
  const { x, y, w } = b;
  const roofColors: Record<string, string> = {
    home: "#957455",
    bakery: "#b46c4b",
    workshop: "#577b70",
    hall: "#617f93",
    greenhouse: "#6e9d91",
    fishery: "#648e9b",
    loom: "#657b98",
    furniture: "#a47f49",
    kitchen: "#98715d",
    teahouse: "#597d74",
    depot: "#747c77",
    apiary: "#ad9150",
  };
  const tone = roofColors[b.kind] ?? "#7e8860";
  // A narrow tiled roof at the back preserves the readable cutaway interiors.
  c.save();
  c.beginPath();
  c.moveTo(x - 7, y + 3);
  c.lineTo(x + w / 2, y - 23);
  c.lineTo(x + w + 7, y + 3);
  c.lineTo(x + w + 7, y + 11);
  c.lineTo(x + w / 2, y - 14);
  c.lineTo(x - 7, y + 11);
  c.closePath();
  c.fillStyle = tone;
  c.fill();
  c.clip();
  const sheen = c.createLinearGradient(x, y - 24, x + w, y + 12);
  sheen.addColorStop(0, "#f3d99e66");
  sheen.addColorStop(0.5, "#e6dba922");
  sheen.addColorStop(0.52, "#274c4c30");
  sheen.addColorStop(1, "#263c3d44");
  c.fillStyle = sheen;
  c.fillRect(x - 8, y - 26, w + 16, 40);
  for (let xx = x - 7; xx < x + w + 7; xx += 9)
    line(c, [xx, y - 25, xx + 3, y + 12], "#263b3b45", 0.8);
  for (let yy = y - 22; yy < y + 12; yy += 4)
    line(c, [x - 8, yy, x + w + 8, yy], "#efddaf30", 0.6);
  c.restore();
  line(
    c,
    [x - 7, y + 11, x + w / 2, y - 14, x + w + 7, y + 11],
    "#4d5d494d",
    2,
  );
  line(c, [x - 7, y + 2, x + w / 2, y - 24, x + w + 7, y + 2], "#e9d2a4", 1.1);
  if (b.kind === "home" || b.kind === "bakery" || b.kind === "kitchen") {
    const cx = x + w * 0.72;
    box(c, cx + 2, y - 26, 9, 18, "#4c544d44", 1);
    box(c, cx, y - 29, 8, 18, "#986b50", 1);
    for (let yy = y - 25; yy < y - 10; yy += 5)
      line(c, [cx, yy, cx + 8, yy], "#dbc29888", 0.7);
    box(c, cx - 2, y - 31, 12, 4, "#6b5344", 1);
    line(c, [cx - 1, y - 31, cx + 9, y - 31], "#cfaf84", 1);
  }
}

function room(c: Brush, b: Building) {
  const { x, y, w, h } = b;
  buildingShadow(c, b);
  box(c, x + 7, y + 10, w, h, "#52645426", 3);
  box(c, x, y, w, h, "#6d7b6b", 3);
  box(
    c,
    x + 5,
    y + 5,
    w - 10,
    h - 10,
    b.kind === "home" ? "#e6e7d7" : "#dfc696",
    1,
  );
  const stone = ["home", "kitchen", "greenhouse", "hall"].includes(b.kind);
  surface(
    c,
    { x: x + 5, y: y + 5, w: w - 10, h: h - 10 },
    stone ? "stone" : "timber",
    stone ? "#e0ded0" : "#c4a16f",
    x + y,
  );
  contactShade(c, { x: x + 5, y: y + 5, w: w - 10, h: h - 10 });
  // Cutaway wall caps, shadow and windows give the interior depth.
  box(c, x, y, w, 8, "#a6b3a5", 2);
  box(c, x, y, w, 3, "#eef0dd", 1);
  box(c, x, y + 7, 5, h - 7, "#8a9988");
  box(c, x + w - 5, y + 7, 5, h - 7, "#50695e");
  box(c, x + 5, y + h - 5, w - 10, 5, "#c0c8b5");
  box(c, x + w / 2 - 9, y + h - 5, 18, 7, "#e5d4ad");
  for (let xx = x + 19; xx < x + w - 12; xx += 43) {
    box(c, xx, y - 2, 22, 6, "#5b7f86", 1);
    box(c, xx + 2, y - 1, 18, 3, "#c0e2db");
    line(c, [xx + 11, y - 1, xx + 11, y + 2], "#6f9697", 1);
  }
}
export function drawShell(c: Brush, b: Building) {
  room(c, b);
  drawRoof(c, b);
}
