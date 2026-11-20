import { box, ellipse, line } from "./brush";
export type Facing = "front" | "back" | "left" | "right";
export const RESIDENT_COLORS = [
  "#bd7962",
  "#658eab",
  "#9682b0",
  "#c09d52",
  "#70996b",
  "#bc819b",
  "#628d82",
  "#a58863",
  "#7c97a1",
  "#b3937c",
  "#8e9c69",
  "#a489a2",
];
export function makeResidentTexture(
  index: number,
  facing: Facing,
  frame: number,
) {
  const canvas = document.createElement("canvas");
  canvas.width = 144;
  canvas.height = 192;
  const c = canvas.getContext("2d")!;
  c.scale(2, 2);
  c.translate(36, 86);
  const side = facing === "left" || facing === "right",
    back = facing === "back";
  if (facing === "left") c.scale(-1, 1);
  const stride = frame ? Math.sin(((frame - 1) * Math.PI) / 2) * 3 : 0;
  const bob = frame ? Math.abs(stride) * 0.25 : 0;
  const skin = ["#ebc5a0", "#dbb18c", "#c99c7a"][index % 3];
  const hair = ["#4c493e", "#65503f", "#7b5a43", "#454c4e"][index % 4];
  const shirt = RESIDENT_COLORS[index % 12];
  c.translate(0, -bob);
  // Rounded limbs, shoe soles and a tapered silhouette remain crisp when zoomed.
  line(c, [-5, -14, -5 + stride, 0], "#47595c", 6);
  line(c, [5, -14, 5 - stride, -1], "#536567", 6);
  box(c, -9 + stride, -2, 9, 4, "#f4edd6", 2);
  box(c, 1 - stride, -3, 9, 4, "#f4edd6", 2);
  line(c, [-10, -32, -13 - stride, -19], "#b99476", 5);
  line(c, [10, -32, 13 + stride, -19], skin, 5);
  box(c, -11, -38, 22, 25, shirt, 6);
  box(c, -8, -35, 4, 18, "#ffffff26", 2);
  if (back) {
    line(c, [-6, -32, 6, -32], "#ffffff3b", 1);
    box(c, -7, -30, 14, 15, "#d0b489", 3);
    line(c, [-7, -36, -7, -23, 7, -23, 7, -36], "#826f5866", 1.5);
  }
  ellipse(c, 0, -51, 13, 14, hair);
  ellipse(c, side ? 3 : 0, -49, 11, 12, skin);
  ellipse(c, -2, -58, 12, 7, hair);
  box(c, -12, -56, 4, 12, hair, 2);
  if (back) {
    ellipse(c, 0, -50, 12, 12, hair);
  } else if (side) {
    ellipse(c, 11, -48, 3, 3, skin);
    ellipse(c, 7, -51, 1.2, 1.7, "#394d49");
    line(c, [6, -43, 9, -43], "#af7c66", 1);
  } else {
    ellipse(c, -4, -50, 1.2, 1.7, "#394d49");
    ellipse(c, 5, -50, 1.2, 1.7, "#394d49");
    line(c, [-2, -43, 2, -42, 5, -43], "#ac7d67", 1);
    if (index === 1 || index === 4) {
      c.strokeStyle = "#52605b";
      c.lineWidth = 1;
      for (const x of [-8, 2]) {
        c.beginPath();
        c.roundRect(x, -54, 7, 7, 2);
        c.stroke();
      }
      line(c, [-1, -51, 2, -51], "#52605b", 1);
    }
  }
  if (index % 4 === 0) {
    box(c, -15, -62, 30, 4, "#bb9a65", 2);
    box(c, -10, -71, 20, 11, "#e5ca8a", 4);
    box(c, -10, -63, 20, 3, "#9b8460", 1);
  } else if (index === 5) {
    ellipse(c, 12, -55, 5, 6, hair);
  }
  return canvas;
}
