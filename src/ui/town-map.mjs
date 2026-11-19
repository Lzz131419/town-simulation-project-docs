// Original pixel artwork, drawn locally. Presentation positions are not world state.
// Keep the logical map at 1024×672 for stable hit-testing and simulation
// coordinates, then render the artwork on a 2× backing surface.  The
// supersampled background keeps the hand-drawn pixel shapes clear when the
// desktop map grows beyond its original viewport.
const WIDTH = 1024,
  HEIGHT = 672,
  ART_SCALE = 2;
const COLORS = [
  "#cf7857",
  "#5f9eb0",
  "#9680be",
  "#e2b858",
  "#6d9b64",
  "#ce7896",
  "#4a9688",
  "#a57954",
];
const placeIcons = {
  farm: "✦",
  well: "≈",
  market: "◉",
  plaza: "···",
  home: "休",
};
export const locations = {
  farm: {
    label: "河畔农田",
    x: 160,
    y: 320,
    facilityId: "farm-01",
    description: "生产粮食",
  },
  well: {
    label: "老水井",
    x: 785,
    y: 340,
    facilityId: "well-01",
    description: "取水与补给",
  },
  market: {
    label: "雾河集市",
    x: 505,
    y: 220,
    facilityId: "market-01",
    description: "购买粮食",
  },
  plaza: {
    label: "中央广场",
    x: 506,
    y: 420,
    facilityId: "plaza-01",
    description: "居民社交",
  },
  home: {
    label: "居民住宅",
    x: 325,
    y: 566,
    facilityId: "home-01",
    description: "居民休息",
  },
};
const rect = (c, color, x, y, w, h) => {
  c.fillStyle = color;
  c.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
};
// Half-logical-pixel details resolve to whole pixels on the 2× art surface.
// They add actual texture detail without enlarging the original tile shapes.
const detailRect = (c, color, x, y, w, h) => {
  c.fillStyle = color;
  c.fillRect(
    Math.round(x * 2) / 2,
    Math.round(y * 2) / 2,
    Math.round(w * 2) / 2,
    Math.round(h * 2) / 2,
  );
};
function tree(c, x, y, size = 1) {
  c.save();
  c.translate(x, y);
  c.scale(size, size);
  rect(c, "#8bd56d", -14, 15, 31, 7);
  rect(c, "#986f4f", -3, 7, 7, 17);
  rect(c, "#bf8c58", -1, 10, 2, 14);
  rect(c, "#567f70", -14, -18, 29, 33);
  rect(c, "#567f70", -19, -8, 39, 17);
  rect(c, "#567f70", -9, -25, 20, 43);
  rect(c, "#6b9f7b", -15, -15, 29, 28);
  rect(c, "#70a982", -17, -6, 34, 13);
  rect(c, "#80b675", -11, -21, 22, 23);
  rect(c, "#99ce7d", -7, -23, 13, 13);
  rect(c, "#8cc37d", -14, -9, 12, 12);
  rect(c, "#609b79", 7, -4, 10, 14);
  rect(c, "#77ad7d", -7, 4, 19, 10);
  // Scattered leaf facets, finer than the canopy's stepped outline.
  for (const [dx, dy, light] of [
    [-5.5, -20.5, true], [1.5, -18, true], [7, -13.5, true],
    [-10.5, -11, true], [-14, -3.5, false], [-4.5, -6, true],
    [3, -3.5, false], [10.5, 1, true], [-8, 5.5, false],
    [-1.5, 9, true], [7, 8, false], [13, 4.5, false],
  ]) {
    detailRect(c, light ? "#a1d48a" : "#5c9675", dx, dy, 3.5, 1);
    detailRect(c, light ? "#8bc480" : "#659e79", dx + 1, dy + 1, 1.5, 1);
  }
  detailRect(c, "#d49c62", 1.5, 17, 1, 5);
  c.restore();
}
function fence(c, x, y, w, h) {
  const line = (x1, y1, x2, y2) => {
    rect(c, "#896e4b", x1, y1, x2 - x1 || 3, y2 - y1 || 3);
  };
  line(x, y + 4, x + w, y + 4);
  line(x, y + 10, x + w, y + 10);
  for (let i = 0; i <= w; i += 22) {
    rect(c, "#b29a68", x + i, y - 3, 5, 19);
    rect(c, "#e0cb95", x + i, y - 3, 5, 3);
  }
  if (h) {
    for (let i = 0; i <= h; i += 22) {
      rect(c, "#b29a68", x, y + i, 5, 5);
      rect(c, "#b29a68", x + w, y + i, 5, 5);
    }
    line(x, y, x, y + h);
    line(x + w, y, x + w, y + h);
  }
}
function bed(c, x, y, color) {
  rect(c, "#715a45", x - 2, y - 2, 27, 42);
  rect(c, "#ece4c6", x, y, 23, 36);
  rect(c, "#fbf3dd", x + 2, y + 2, 19, 9);
  rect(c, color, x, y + 13, 23, 23);
  rect(c, "#ffffff45", x + 3, y + 15, 4, 18);
  rect(c, "#8d7450", x - 3, y + 34, 29, 5);
}
function shelf(c, x, y, w = 37) {
  rect(c, "#715944", x, y, w, 20);
  rect(c, "#bd9d6d", x + 2, y + 2, w - 4, 16);
  for (let i = 0; i < w - 7; i += 6)
    rect(c, COLORS[(i / 6) % 8], x + 4 + i, y + 4, 4, 11);
  rect(c, "#d5bc89", x, y + 15, w, 4);
}
function table(c, x, y, w = 28, h = 20) {
  rect(c, "#806547", x + 3, y + 5, w, h);
  rect(c, "#d6b477", x, y, w, h);
  rect(c, "#ead097", x + 2, y + 1, w - 4, 3);
  rect(c, "#759567", x + w / 2 - 3, y + 7, 7, 5);
}
function house(c, x, y, w, h, roof, kind = "home") {
  const floor = kind === "home"
    ? ["#f0edc4", "#d9eddf", "#e8e3d1"][Math.floor(x) % 3]
    : "#e8c788";
  rect(c, "#80bc6950", x + 8, y + 10, w + 4, h + 9);
  rect(c, "#545c64", x - 4, y - 4, w + 8, h + 8);
  rect(c, floor, x, y, w, h);
  for (let row = 18; row < h - 6; row += 10) {
    detailRect(c, kind === "home" ? "#c4c5ad" : "#ba9765", x + 6, y + row, w - 12, 0.5);
    detailRect(c, "#fff7d366", x + 6, y + row + 1, w - 12, 0.5);
    for (let col = 10 + (row % 20); col < w - 9; col += 28) {
      detailRect(c, "#b6b79d88", x + col, y + row, 0.5, 10);
      detailRect(c, "#fffbe480", x + col + 2, y + row + 3, 9.5, 1);
      if (kind !== "home")
        detailRect(c, "#bd9869", x + col + 5, y + row + 6.5, 4, 0.5);
    }
  }
  rect(c, roof, x - 8, y - 12, w + 16, 20);
  rect(c, "#f6f5e8", x - 8, y - 12, w + 16, 3);
  rect(c, "#60616a", x - 8, y + 4, w + 16, 4);
  for (let col = 0; col < w; col += 12)
    detailRect(c, "#74778166", x + col + 0.5, y - 9, 0.5, 12);
  rect(c, "#f6f5e9", x, y + 8, 6, h - 8);
  rect(c, "#b8bac1", x + w - 6, y + 8, 6, h - 8);
  rect(c, "#a2a4aa", x, y + h - 6, w, 6);
  detailRect(c, "#faf9ed", x + 1, y + h - 5.5, w - 2, 1);
  detailRect(c, "#727985", x + 5.5, y + 8, 0.5, h - 14);
  detailRect(c, "#f7f7ee", x + w - 5, y + 8, 1, h - 14);
  rect(c, "#f3e3ac", x + w / 2 - 10, y + h - 7, 20, 11);
  rect(c, "#586979", x + 20, y - 1, 24, 5);
  rect(c, "#acd7db", x + 22, y, 9, 3);
  rect(c, "#acd7db", x + 33, y, 9, 3);
  detailRect(c, "#e7f5f1", x + 22.5, y + 0.5, 7, 0.5);
  detailRect(c, "#e7f5f1", x + 33.5, y + 0.5, 7, 0.5);
  if (kind === "home") {
    bed(
      c,
      x + 12,
      y + 17,
      ["#88b8c3", "#b694ba", "#a4bd72"][Math.floor(x) % 3],
    );
    shelf(c, x + w - 49, y + 13);
    table(c, x + w - 49, y + 48, 31, 20);
    rect(c, "#869ca0", x + 47, y + 30, 24, 35);
    rect(c, "#c6d4bc", x + 50, y + 33, 18, 29);
    for (let stripe = 0; stripe < 5; stripe++)
      detailRect(c, "#f6efd4", x + 51, y + 35 + stripe * 5, 16, 0.5);
    detailRect(c, "#e9eaf0", x + 14, y + 19.5, 18, 0.5);
    detailRect(c, "#6e6e8155", x + 14, y + 45.5, 18, 0.5);
    detailRect(c, "#ece4ce", x + w - 44.5, y + 51, 21, 0.5);
    detailRect(c, "#725641", x + w - 44, y + 23.5, 27, 0.5);
  }
  if (kind === "market") {
    shelf(c, x + 12, y + 17, 70);
    shelf(c, x + w - 83, y + 17, 70);
    table(c, x + 20, y + 60, 60, 24);
    table(c, x + w - 79, y + 60, 60, 24);
    for (let i = 0; i < 5; i++) {
      rect(c, "#c4cf74", x + 24 + i * 10, y + 63, 6, 7);
      rect(c, "#bd7356", x + w - 74 + i * 10, y + 63, 6, 7);
    }
    rect(c, "#849f84", x + w / 2 - 16, y + 32, 32, 48);
    rect(c, "#c6d7a5", x + w / 2 - 13, y + 35, 26, 42);
    for (let stripe = 0; stripe < 7; stripe++)
      detailRect(c, "#e4e8bd", x + w / 2 - 11, y + 38 + stripe * 5, 22, 0.5);
    for (let col = 0; col < 6; col++) {
      detailRect(c, "#ffe9a4", x + 24 + col * 8.5, y + 64, 1.5, 1);
      detailRect(c, "#e6a479", x + w - 74 + col * 8.5, y + 64, 1.5, 1);
    }
  }
  if (kind === "shed") {
    shelf(c, x + 10, y + 14, 40);
    rect(c, "#9a7950", x + w - 38, y + 18, 25, 25);
    rect(c, "#c9a873", x + w - 36, y + 20, 21, 21);
    for (let i = 0; i < 3; i++)
      rect(c, "#a3b884", x + 12 + i * 10, y + 43, 7, 12);
  }
}
function bench(c, x, y, vertical = false) {
  c.save();
  c.translate(x, y);
  if (vertical) c.rotate(Math.PI / 2);
  rect(c, "#6e654b", 2, 2, 27, 14);
  rect(c, "#b39160", 0, 0, 30, 5);
  rect(c, "#cfac70", 0, 8, 30, 5);
  rect(c, "#6f6250", 3, 14, 4, 3);
  rect(c, "#6f6250", 23, 14, 4, 3);
  c.restore();
}
function flower(c, x, y, color = "#d18b80") {
  rect(c, "#648352", x, y, 3, 7);
  rect(c, color, x - 2, y - 2, 7, 5);
  rect(c, "#e8dba6", x, y - 1, 2, 2);
}
function lamp(c, x, y) {
  rect(c, "#5c675a", x - 1, y - 18, 3, 20);
  rect(c, "#4e5a51", x - 5, y - 22, 11, 8);
  rect(c, "#f4dea0", x - 3, y - 20, 7, 5);
  rect(c, "#4e5a51", x - 3, y + 1, 7, 3);
}
function baseMap() {
  const canvas = document.createElement("canvas");
  canvas.width = WIDTH * ART_SCALE;
  canvas.height = HEIGHT * ART_SCALE;
  const c = canvas.getContext("2d");
  c.scale(ART_SCALE, ART_SCALE);
  c.imageSmoothingEnabled = false;
  rect(c, "#a4f773", 0, 0, WIDTH, HEIGHT);
  for (let y = 0; y < HEIGHT; y += 8)
    for (let x = 0; x < WIDTH; x += 8) {
      const k = (x * 17 + y * 31 + x * y) % 107;
      if (k < 8)
        detailRect(c, k % 2 ? "#bafc89" : "#97e56c", x + 2.5, y + 3.5, 2, 0.5);
      if (k === 4) {
        detailRect(c, "#6eb96c", x + 1.5, y, 0.5, 2.5);
        detailRect(c, "#78c474", x + 3, y + 1.5, 0.5, 1.5);
        detailRect(c, "#8ad577", x + 1.5, y + 2.5, 2, 0.5);
      }
      if (k === 44) {
        detailRect(c, "#e8fba3", x + 3.5, y + 2, 1, 1);
        detailRect(c, "#f3ffbb", x + 4.5, y + 1.5, 1, 1);
      }
    }
  // Riverbank and small wooden footbridge.
  for (let y = 0; y < HEIGHT; y += 16) {
    const edge = 915 + Math.round((Math.sin(y / 96) * 14) / 8) * 8;
    rect(c, "#e2dfa0", edge - 8, y, WIDTH - edge + 8, 16);
    rect(c, "#5b9fa3", edge, y, WIDTH - edge, 16);
    rect(c, "#82c4c3", edge + 5, y, WIDTH - edge - 5, 16);
    if (y % 32 === 0)
      for (let x = edge + 15; x < WIDTH; x += 37)
        detailRect(c, "#c0e4d4", x + 0.5, y + 9.5, 17, 0.5);
  }
  const path = (x, y, w, h) => {
    rect(c, "#e5ed91", x - 3, y - 3, w + 6, h + 6);
    rect(c, "#fff99a", x, y, w, h);
    for (let yy = y + 4; yy < y + h; yy += 13)
      for (let xx = x + 5; xx < x + w; xx += 22)
        detailRect(c, "#e8e79b", xx + 0.5, yy + 0.5, 1.5, 0.5);
  };
  path(70, 278, 880, 38);
  path(305, 42, 37, 578);
  path(663, 67, 38, 558);
  path(140, 477, 650, 34);
  path(316, 145, 366, 28);
  path(488, 275, 35, 236);
  path(150, 412, 175, 25);
  path(760, 310, 30, 182);
  rect(c, "#765e42", 906, 277, 118, 41);
  for (let x = 907; x < 1024; x += 9) {
    rect(c, "#bd9964", x, 279, 7, 37);
    rect(c, "#dec28b", x, 279, 7, 3);
  }
  rect(c, "#735c41", 905, 271, 119, 5);
  rect(c, "#735c41", 905, 320, 119, 5);
  // Northern homes, shop, field shed and residential lane.
  house(c, 166, 58, 115, 91, "#c8c8c9");
  house(c, 370, 48, 108, 95, "#c1c8d0");
  house(c, 535, 48, 105, 95, "#d0cbc7");
  house(c, 745, 76, 111, 105, "#c8cec4");
  house(c, 404, 192, 210, 100, "#c9c5c6", "market");
  house(c, 76, 197, 160, 65, "#c5c8c1", "shed");
  for (let y = 329; y < 407; y += 22)
    for (let x = 83; x < 255; x += 24) {
      rect(c, "#a7784e", x, y, 20, 17);
      rect(c, "#d7a16a", x, y + 2, 20, 4);
      rect(c, "#568f54", x + 7, y + 3, 4, 11);
      rect(c, "#6caf5d", x + 3, y + 3, 12, 5);
      rect(c, "#a4d879", x + 7, y, 4, 6);
      detailRect(c, "#d0e69a", x + 7.5, y + 1, 1, 4);
      detailRect(c, "#866044", x + 1, y + 13.5, 17, 0.5);
    }
  fence(c, 71, 321, 195, 89);
  fence(c, 72, 411, 195, 0);
  // Plaza stone tiles, fountain, benches and gardens.
  rect(c, "#76a76f", 381, 336, 245, 130);
  rect(c, "#d6d8c6", 388, 340, 231, 121);
  for (let y = 343; y < 461; y += 16)
    for (let x = 390; x < 619; x += 18) {
      rect(c, (x + y) % 5 ? "#ece9cf" : "#c7cbbd", x, y, 16, 14);
      detailRect(c, "#aeb9af", x + 1, y + 1, 14, 0.5);
    }
  rect(c, "#717d84", 486, 371, 53, 52);
  rect(c, "#f5edbe", 481, 376, 63, 42);
  rect(c, "#b8c9bb", 486, 380, 53, 34);
  rect(c, "#6aa8a2", 490, 384, 45, 25);
  rect(c, "#a9d3bd", 495, 388, 34, 3);
  rect(c, "#e3e4d4", 507, 377, 11, 27);
  rect(c, "#fff3c6", 503, 372, 19, 9);
  rect(c, "#c4e5c3", 507, 368, 11, 6);
  detailRect(c, "#ffffff", 492, 385, 40, 0.5);
  detailRect(c, "#438887", 497, 392, 30, 0.5);
  bench(c, 410, 352);
  bench(c, 568, 352);
  bench(c, 411, 438);
  bench(c, 567, 438);
  lamp(c, 382, 341);
  lamp(c, 626, 341);
  lamp(c, 382, 463);
  lamp(c, 626, 463);
  for (let i = 0; i < 7; i++) {
    flower(c, 401 + i * 30, 332, i % 2 ? "#e5c56e" : "#ce8c85");
    flower(c, 401 + i * 30, 467);
  }
  // Well and water court.
  rect(c, "#d5d4b4", 741, 339, 105, 98);
  for (let y = 343; y < 434; y += 16)
    for (let x = 746; x < 843; x += 18) rect(c, "#f0e7c4", x, y, 14, 12);
  rect(c, "#687b78", 767, 361, 47, 38);
  rect(c, "#c4cbc0", 762, 366, 57, 26);
  rect(c, "#f2edcf", 766, 362, 49, 8);
  rect(c, "#5f999c", 774, 370, 32, 16);
  rect(c, "#9fd0c0", 779, 372, 22, 4);
  rect(c, "#725b4c", 758, 343, 5, 45);
  rect(c, "#725b4c", 818, 343, 5, 45);
  rect(c, "#8b684e", 753, 333, 74, 13);
  rect(c, "#c09862", 758, 328, 64, 8);
  rect(c, "#5f5245", 790, 344, 3, 27);
  rect(c, "#d0ab6d", 787, 367, 11, 8);
  detailRect(c, "#fbefc8", 755, 335, 69, 0.5);
  bench(c, 765, 416);
  house(c, 158, 541, 113, 85, "#c8c3ca");
  house(c, 367, 541, 111, 85, "#c1c9c8");
  house(c, 535, 541, 110, 85, "#cdc8c5");
  house(c, 737, 536, 112, 88, "#c3c5ce");
  // Orchard and town boundary: deliberate gaps keep entrances readable.
  for (const [x, y] of [
    [41, 65],
    [86, 58],
    [122, 88],
    [47, 112],
    [91, 121],
    [41, 166],
    [878, 80],
    [895, 135],
    [883, 208],
    [55, 464],
    [91, 481],
    [60, 538],
    [98, 577],
    [45, 621],
    [112, 642],
    [883, 568],
    [888, 627],
    [859, 479],
    [714, 218],
    [863, 258],
    [363, 213],
    [361, 256],
    [711, 567],
    [707, 607],
    [35, 293],
    [34, 359],
    [37, 415],
  ])
    tree(c, x, y, 1);
  for (let x = 170; x < 858; x += 47) {
    if ((x > 290 && x < 355) || (x > 640 && x < 716)) continue;
    tree(c, x, 650, 0.75);
  }
  for (let x = 165; x < 885; x += 55) tree(c, x, 24, 0.75);
  for (const [x, y] of [
    [352, 474],
    [703, 472],
    [279, 176],
    [634, 176],
    [874, 408],
    [66, 291],
  ]) {
    rect(c, "#8a8156", x, y, 14, 14);
    rect(c, "#6e9550", x - 4, y - 10, 22, 20);
    flower(c, x + 4, y - 5, "#d7ad76");
  }
  for (let i = 0; i < 8; i++)
    flower(c, 349 + i * 4, 415 + (i % 3) * 7, "#ddd38e");
  return canvas;
}
export function drawAvatar(c, x, y, index, scale = 2, walking = 0) {
  const color = COLORS[index % COLORS.length],
    skins = ["#e9bf93", "#d7a077", "#bf875f"],
    skin = skins[index % 3],
    hair = ["#51483c", "#785237", "#b58d4c", "#3f4548"][index % 4];
  c.save();
  c.translate(Math.round(x), Math.round(y));
  c.scale(scale, scale);
  rect(c, "#526a4d55", -5, 1, 11, 3);
  const stride = walking ? Math.sin(walking) * 1.3 : 0;
  rect(c, "#3f484c", -3, -3, 3, 5 + stride);
  rect(c, "#3f484c", 1, -3, 3, 5 - stride);
  rect(c, "#ebe4cb", -4, 2 + stride, 4, 2);
  rect(c, "#ebe4cb", 1, 2 - stride, 4, 2);
  rect(c, color, -4, -10, 9, 8);
  rect(c, skin, -6, -9, 2, 6);
  rect(c, skin, 5, -9, 2, 6);
  rect(c, "#ffffff38", -3, -10, 2, 7);
  rect(c, hair, -5, -19, 11, 10);
  rect(c, hair, -6, -16, 13, 6);
  rect(c, skin, -4, -16, 9, 8);
  rect(c, hair, -5, -19, 11, 4);
  rect(c, hair, -5, -16, 3, 3);
  rect(c, "#37433b", -2, -12, 1, 2);
  rect(c, "#37433b", 3, -12, 1, 2);
  rect(c, "#b78165", 0, -9, 2, 1);
  if (index % 5 === 0) {
    rect(c, "#d9bd78", -6, -19, 13, 3);
    rect(c, "#ead294", -4, -23, 9, 5);
    rect(c, "#846c46", -4, -20, 9, 1);
  }
  c.restore();
}
export function portrait(canvas, index) {
  const c = canvas.getContext("2d");
  c.clearRect(0, 0, canvas.width, canvas.height);
  c.imageSmoothingEnabled = false;
  const scale = Math.min(
    2.3,
    (canvas.height - 4) / 27,
    (canvas.width - 4) / 13,
  );
  drawAvatar(c, canvas.width / 2, canvas.height - 4 * scale - 2, index, scale);
}
export function presentationFor(agent, events, day) {
  const own = events.filter(
    (e) => e.day === day && e.actorIds.includes(agent.agentId),
  );
  const social = own.some((e) => e.type === "SOCIAL_INTERACTION"),
    worked = own.some((e) => e.type === "WORKED"),
    rested = own.some((e) => e.type === "RESTED");
  if (day === 0)
    return {
      place:
        agent.jobCode === "farmer"
          ? "farm"
          : agent.jobCode === "waterWorker"
            ? "well"
            : "home",
      action: "准备开始一天",
      icon: "…",
    };
  if (social)
    return { place: "plaza", action: "在广场与邻居交往", icon: "···" };
  if (worked)
    return agent.jobCode === "farmer"
      ? { place: "farm", action: "在农田完成生产", icon: "✦" }
      : { place: "well", action: "在水井完成取水", icon: "≈" };
  if (rested) return { place: "home", action: "在住宅休息", icon: "休" };
  return { place: "market", action: "完成今日生活安排", icon: "·" };
}

export function dailyJourney(agent, events, day) {
  const own = events
      .filter(
        (event) => event.day === day && event.actorIds.includes(agent.agentId),
      )
      .sort((a, b) => a.sequence - b.sequence),
    places = [];
  const add = (place) => {
    if (places.at(-1) !== place) places.push(place);
  };
  if (day === 0) {
    add(
      agent.jobCode === "farmer"
        ? "farm"
        : agent.jobCode === "waterWorker"
          ? "well"
          : "home",
    );
  }
  for (const event of own) {
    if (event.type === "WORKED")
      add(agent.jobCode === "farmer" ? "farm" : "well");
    else if (
      [
        "FOOD_PURCHASED",
        "FOOD_OUT_OF_STOCK",
        "INSUFFICIENT_PERSONAL_FUNDS",
      ].includes(event.type)
    )
      add("market");
    else if (["WATER_CONSUMED", "WATER_OUT_OF_STOCK"].includes(event.type))
      add("well");
    else if (event.type === "SOCIAL_INTERACTION") add("plaza");
    else if (event.type === "RESTED") add("home");
  }
  if (!places.length) add(presentationFor(agent, events, day).place);
  return places;
}

const ROUTE_OFFSETS = {
  farm: [
    [0, 0],
    [12, -5],
    [20, 4],
    [8, 11],
    [-8, 7],
    [-14, -3],
  ],
  well: [
    [0, 0],
    [12, -4],
    [20, 5],
    [9, 12],
    [-8, 8],
    [-15, -2],
  ],
  market: [
    [0, 0],
    [12, -5],
    [20, 3],
    [10, 11],
    [-8, 9],
    [-16, 1],
  ],
  plaza: [
    [0, 0],
    [10, -6],
    [18, 2],
    [9, 10],
    [-7, 8],
    [-15, 0],
  ],
  home: [
    [0, 0],
    [10, -4],
    [16, 5],
    [7, 11],
    [-8, 7],
    [-13, -2],
  ],
};

function anchor(place, index) {
  const groups = {
    farm: [
      [88, 354],
      [130, 354],
      [172, 354],
      [214, 354],
      [256, 354],
      [88, 399],
      [130, 399],
      [172, 399],
      [214, 399],
      [256, 399],
    ],
    well: [
      [738, 349],
      [785, 349],
      [832, 349],
      [872, 349],
      [736, 402],
      [837, 402],
      [875, 402],
      [746, 452],
      [794, 452],
      [840, 452],
    ],
    market: [
      [430, 308],
      [475, 308],
      [520, 308],
      [565, 308],
      [610, 308],
    ],
    plaza: [
      [414, 390],
      [458, 390],
      [554, 390],
      [598, 390],
      [414, 440],
      [458, 440],
      [508, 440],
      [554, 440],
      [598, 440],
      [508, 354],
    ],
    home: [
      [183, 520],
      [245, 520],
      [380, 520],
      [442, 520],
      [550, 520],
      [613, 520],
      [750, 516],
      [815, 516],
      [322, 195],
      [683, 235],
    ],
  };
  const points = groups[place] ?? groups.home;
  const point = points[index % points.length];
  return { x: point[0], y: point[1] + Math.floor(index / points.length) * 33 };
}

export function activityRoute(place, slot) {
  const base = anchor(place, slot),
    offsets = ROUTE_OFFSETS[place] ?? ROUTE_OFFSETS.home,
    shift = slot % offsets.length;
  return offsets.map((_, index) => {
    const [x, y] = offsets[(index + shift) % offsets.length];
    return { x: base.x + x, y: base.y + y };
  });
}

export function layoutResidents(agents, events, day) {
  const slots = {};
  return agents.map((agent, index) => {
    const activity = presentationFor(agent, events, day);
    const slot = slots[activity.place] ?? 0;
    slots[activity.place] = slot + 1;
    const journey = dailyJourney(agent, events, day).map(
      (place, journeyIndex) => {
        const journeySlot =
          place === activity.place ? slot : (index + journeyIndex) % 10;
        return {
          place,
          anchor: anchor(place, journeySlot),
          route: activityRoute(place, journeySlot),
        };
      },
    );
    return {
      id: agent.agentId,
      name: agent.displayName,
      index,
      slot,
      activity,
      socialPartners: [
        ...new Set(events
          .filter((event) => event.day === day &&
            event.type === "SOCIAL_INTERACTION" &&
            event.actorIds.includes(agent.agentId))
          .flatMap((event) => event.actorIds.filter((id) => id !== agent.agentId))),
      ],
      to: anchor(activity.place, slot),
      route: activityRoute(activity.place, slot),
      journey,
    };
  });
}

const LEG_MS = 5200;
const DWELL_FRACTION = 0.2;
const smooth = (value) => value * value * (3 - 2 * value);

// View-only motion. Local wandering is an offset from a facility, never a
// second absolute destination. Its weight is zero at both ends of a journey
// leg, so changing facilities (including the last-to-first leg) is continuous.
export function residentMotion(person, time, reduced = false) {
  const journey = person.journey?.length
    ? person.journey
    : [{ place: person.activity.place, anchor: person.to, route: person.route }];
  if (reduced) {
    const last = journey.at(-1);
    return {
      ...last.anchor,
      currentPlace: last.place,
      moving: false,
      inTransit: false,
    };
  }
  if (journey.length === 1) {
    const stop = journey[0],
      route = stop.route?.length ? stop.route : [stop.anchor],
      phase = (time / LEG_MS + person.index * 0.23) % route.length,
      index = Math.floor(phase),
      progress = Math.max(0, (phase - index - DWELL_FRACTION) / (1 - DWELL_FRACTION)),
      from = route[index],
      to = route[(index + 1) % route.length],
      ease = smooth(progress);
    return {
      x: from.x + (to.x - from.x) * ease,
      y: from.y + (to.y - from.y) * ease,
      currentPlace: stop.place,
      moving: progress > 0 && Math.hypot(to.x - from.x, to.y - from.y) > 0,
      inTransit: false,
    };
  }
  const phase = (time / LEG_MS + person.index * 0.17) % journey.length,
    index = Math.floor(phase),
    from = journey[index],
    to = journey[(index + 1) % journey.length],
    progress = Math.max(0, (phase - index - DWELL_FRACTION) / (1 - DWELL_FRACTION)),
    ease = smooth(progress),
    route = from.route?.length ? from.route : [from.anchor],
    roamPhase = (time / 2600 + person.index * 0.23) % route.length,
    roamIndex = Math.floor(roamPhase),
    roamT = roamPhase - roamIndex,
    roamFrom = route[roamIndex],
    roamTo = route[(roamIndex + 1) % route.length],
    weight = Math.sin(Math.PI * progress) ** 2 * 0.35,
    offsetX = roamFrom.x + (roamTo.x - roamFrom.x) * roamT - from.anchor.x,
    offsetY = roamFrom.y + (roamTo.y - roamFrom.y) * roamT - from.anchor.y,
    moving = progress > 0;
  return {
    x: from.anchor.x + (to.anchor.x - from.anchor.x) * ease + offsetX * weight,
    y: from.anchor.y + (to.anchor.y - from.anchor.y) * ease + offsetY * weight,
    currentPlace: moving ? null : from.place,
    moving,
    inTransit: moving,
  };
}

export function visibleSocialPairs(people) {
  const settled = people.filter((person) =>
    person.currentPlace === "plaza" && !person.moving && !person.inTransit);
  return settled.flatMap((a, index) =>
    settled.slice(index + 1)
      .filter((b) => a.socialPartners?.includes(b.id) &&
        b.socialPartners?.includes(a.id) &&
        Math.hypot(a.x - b.x, a.y - b.y) <= 96)
      .map((b) => [a, b]));
}
export function createTownMap(canvas, { onSelect, onLocation }) {
  const ctx = canvas.getContext("2d"),
    background = baseMap();
  let model = [],
    selected = "",
    hover = "",
    zoom = 1,
    pan = { x: 0, y: 0 },
    size = { w: 1, h: 1, dpr: 1 },
    raf,
    drag = null,
    oldDay = -1,
    presentationKey = "",
    showNames = false,
    showActions = true;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const camera = () => ({
    s: Math.min(size.w / WIDTH, size.h / HEIGHT) * zoom,
    x:
      (size.w - WIDTH * Math.min(size.w / WIDTH, size.h / HEIGHT) * zoom) / 2 +
      pan.x,
    y:
      (size.h - HEIGHT * Math.min(size.w / WIDTH, size.h / HEIGHT) * zoom) / 2 +
      pan.y,
  });
  function render(time) {
    const cam = camera();
    ctx.setTransform(size.dpr, 0, 0, size.dpr, 0, 0);
    ctx.clearRect(0, 0, size.w, size.h);
    ctx.fillStyle = "#a4f773";
    ctx.fillRect(0, 0, size.w, size.h);
    ctx.translate(cam.x, cam.y);
    ctx.scale(cam.s, cam.s);
    // Downsample the 2× backing surface once before drawing the characters.
    // This keeps the map details clear at desktop scale without large nearest
    // neighbour blocks, while the residents remain crisp pixel sprites.
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(background, 0, 0, WIDTH, HEIGHT);
    ctx.imageSmoothingEnabled = false;
    for (const [key, location] of Object.entries(locations)) {
      const y =
        key === "farm"
          ? 276
          : key === "market"
            ? 168
            : key === "well"
              ? 304
              : key === "plaza"
                ? 485
                : 637;
      const x = location.x;
      ctx.font = "600 11px system-ui";
      const w = ctx.measureText(location.label).width + 18;
      rect(ctx, "#ffffe9df", x - w / 2, y - 13, w, 20);
      rect(ctx, "#71815b55", x - w / 2, y + 7, w, 2);
      ctx.fillStyle = "#475543";
      ctx.textAlign = "center";
      ctx.fillText(location.label, x, y + 1);
    }
    for (const person of model) {
      const t = reduced ? 1 : Math.min(1, (time - person.start) / 850),
        ease = smooth(t),
        motion = residentMotion(person, time, reduced),
        entering = t < 1 && Math.hypot(motion.x - person.from.x, motion.y - person.from.y) > 0.1;
      person.currentPlace = entering ? null : motion.currentPlace;
      person.moving = entering || motion.moving;
      person.inTransit = entering || motion.inTransit;
      person.x = person.from.x + (motion.x - person.from.x) * ease;
      person.y = person.from.y + (motion.y - person.from.y) * ease;
    }
    const socialPairs = visibleSocialPairs(model);
    if (showActions && socialPairs.length) {
      ctx.save();
      ctx.strokeStyle = "#a4b48b99";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([3, 4]);
      for (const [a, b] of socialPairs) {
        ctx.beginPath();
        ctx.moveTo(a.x, a.y - 13);
        ctx.lineTo(b.x, b.y - 13);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.font = "bold 10px system-ui";
        ctx.fillStyle = "#ad8a6a";
        ctx.textAlign = "center";
        ctx.fillText("·", (a.x + b.x) / 2, (a.y + b.y) / 2 - 16);
        ctx.setLineDash([3, 4]);
      }
      ctx.restore();
    }
    for (const person of [...model].sort((a, b) => a.y - b.y)) {
      const active = person.id === selected,
        pointed = person.id === hover;
      if (active) {
        ctx.strokeStyle = "#fff1a6";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.ellipse(person.x, person.y + 3, 13, 5, 0, 0, Math.PI * 2);
        ctx.stroke();
      }
      drawAvatar(
        ctx,
        person.x,
        person.y,
        person.index,
        1.9,
        person.moving && !reduced ? time / 90 : 0,
      );
      if (
        showActions &&
        !person.moving &&
        !person.inTransit &&
        (active ||
          person.currentPlace === "plaza" ||
          person.index % 4 === 0) &&
        oldDay > 0
      ) {
        rect(ctx, "#fffdf0", person.x - 10, person.y - 56, 22, 17);
        rect(ctx, "#fffdf0", person.x - 2, person.y - 39, 4, 4);
        ctx.font = "bold 13px monospace";
        ctx.fillStyle = "#5b6958";
        ctx.textAlign = "center";
        ctx.fillText(
          placeIcons[person.currentPlace] ?? person.activity.icon,
          person.x + 1,
          person.y - 43,
        );
      }
      if (showNames || active || pointed) {
        ctx.font = `${active ? "600" : "500"} 10px system-ui`;
        const text = person.name,
          w = ctx.measureText(text).width + 10;
        rect(
          ctx,
          active ? "#315c4e" : "#fffde9e6",
          person.x - w / 2,
          person.y + 8,
          w,
          17,
        );
        ctx.fillStyle = active ? "#fff" : "#41573c";
        ctx.textAlign = "center";
        ctx.fillText(text, person.x, person.y + 20);
      }
    }
    raf = requestAnimationFrame(render);
  }
  const observer = new ResizeObserver(() => {
    const r = canvas.getBoundingClientRect();
    size = { w: r.width, h: r.height, dpr: devicePixelRatio || 1 };
    canvas.width = r.width * size.dpr;
    canvas.height = r.height * size.dpr;
  });
  observer.observe(canvas);
  const toWorld = (e) => {
    const b = canvas.getBoundingClientRect(),
      cam = camera();
    return {
      x: (e.clientX - b.left - cam.x) / cam.s,
      y: (e.clientY - b.top - cam.y) / cam.s,
    };
  };
  const hit = (p) =>
    [...model]
      .reverse()
      .find(
        (a) => Math.abs(a.x - p.x) < 16 && p.y > a.y - 40 && p.y < a.y + 25,
      );
  canvas.addEventListener("pointerdown", (e) => {
    drag = { x: e.clientX, y: e.clientY, pan: { ...pan }, moved: false };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (drag) {
      const dx = e.clientX - drag.x,
        dy = e.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 5) drag.moved = true;
      if (drag.moved) pan = { x: drag.pan.x + dx, y: drag.pan.y + dy };
    } else {
      const person = hit(toWorld(e));
      hover = person?.id ?? "";
      canvas.style.cursor = person ? "pointer" : "grab";
    }
  });
  canvas.addEventListener("pointerup", (e) => {
    if (drag && !drag.moved) {
      const point = toWorld(e),
        person = hit(point);
      if (person) onSelect(person.id);
      else {
        const nearest = Object.entries(locations).find(
          ([, l]) =>
            Math.abs(l.x - point.x) < 90 && Math.abs(l.y - point.y) < 60,
        );
        if (nearest) onLocation(nearest[0]);
      }
    }
    drag = null;
  });
  canvas.addEventListener("pointercancel", () => (drag = null));
  canvas.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      zoom = Math.max(0.75, Math.min(2.5, zoom * (e.deltaY < 0 ? 1.1 : 0.9)));
    },
    { passive: false },
  );
  canvas.addEventListener("keydown", (e) => {
    const moves = {
      ArrowLeft: [30, 0],
      ArrowRight: [-30, 0],
      ArrowUp: [0, 30],
      ArrowDown: [0, -30],
    };
    if (moves[e.key]) {
      e.preventDefault();
      pan.x += moves[e.key][0];
      pan.y += moves[e.key][1];
    }
    if (e.key === "Escape") {
      pan = { x: 0, y: 0 };
      zoom = 1;
    }
  });
  raf = requestAnimationFrame(render);
  return {
    update(agents, events, day, current) {
      const now = performance.now();
      selected = current;
      const next = layoutResidents(agents, events, day);
      const key = JSON.stringify([day, next]);
      if (key === presentationKey) return;
      presentationKey = key;
      const previous = new Map(model.map((a) => [a.id, a]));
      model = next.map((person) => {
        const old = previous.get(person.id);
        return {
          ...person,
          from: old ? { x: old.x, y: old.y } : person.to,
          x: old?.x ?? person.to.x,
          y: old?.y ?? person.to.y,
          start: now,
        };
      });
      oldDay = day;
    },
    select: (id) => (selected = id),
    zoom: (delta) => (zoom = Math.max(0.75, Math.min(2.5, zoom + delta))),
    reset: () => {
      zoom = 1;
      pan = { x: 0, y: 0 };
    },
    names: (value) => (showNames = value),
    actions: (value) => (showActions = value),
    dispose: () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
    },
  };
}
