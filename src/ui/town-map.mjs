// Original pixel artwork, drawn locally. Presentation positions are not world state.
const WIDTH = 1024,
  HEIGHT = 672;
const COLORS = [
  "#c87953",
  "#638c9a",
  "#8776aa",
  "#d9a755",
  "#759162",
  "#bb6b7e",
  "#527c70",
  "#926b51",
];
export const locations = {
  farm: {
    label: "河畔农田",
    x: 160,
    y: 320,
    facilityId: "farm-01",
    description: "农夫在这里生产粮食。每日劳动产粮4份，工资最高2镇币。",
  },
  well: {
    label: "老水井",
    x: 785,
    y: 340,
    facilityId: "well-01",
    description: "取水工在这里生产清水。维修议案可一次性补充30份清水。",
  },
  market: {
    label: "雾河集市",
    x: 505,
    y: 220,
    facilityId: "market-01",
    description: "居民用2镇币购买1份粮食，款项进入公共资金。",
  },
  plaza: {
    label: "中央广场",
    x: 506,
    y: 420,
    facilityId: "plaza-01",
    description: "每天最多10名合格居民按稳定编号配对，增进双向关系。",
  },
  home: {
    label: "居民住宅",
    x: 325,
    y: 566,
    facilityId: "home-01",
    description: "住宅区容纳全体居民。普通居民或精力不足者休息恢复精力。",
  },
};
const rect = (c, color, x, y, w, h) => {
  c.fillStyle = color;
  c.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
};
function tree(c, x, y, size = 1) {
  c.save();
  c.translate(x, y);
  c.scale(size, size);
  rect(c, "#759b60", -15, 13, 34, 10);
  rect(c, "#755e42", -3, 4, 7, 20);
  rect(c, "#536e4c", -16, -14, 32, 29);
  rect(c, "#536e4c", -10, -25, 20, 44);
  rect(c, "#6b8c53", -19, -8, 35, 17);
  rect(c, "#789b57", -13, -21, 25, 28);
  rect(c, "#8cab61", -9, -23, 15, 8);
  rect(c, "#93b06b", -15, -10, 8, 7);
  rect(c, "#516f47", 8, -5, 8, 18);
  rect(c, "#64864c", -7, 7, 19, 10);
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
  rect(c, "#779364", x + 8, y + 10, w + 4, h + 9);
  rect(c, "#59625a", x - 4, y - 4, w + 8, h + 8);
  rect(c, "#eee0b6", x, y, w, h);
  for (let row = 18; row < h; row += 10) {
    rect(c, "#dbc595", x + 3, y + row, w - 6, 1);
    for (let col = 10 + (row % 20); col < w; col += 28)
      rect(c, "#dbc595", x + col, y + row, 1, 10);
  }
  rect(c, roof, x - 8, y - 12, w + 16, 20);
  rect(c, "#ffffff24", x - 8, y - 12, w + 16, 3);
  rect(c, "#00000022", x - 8, y + 4, w + 16, 4);
  for (let col = 0; col < w; col += 12)
    rect(c, "#00000018", x + col, y - 10, 1, 14);
  rect(c, "#ede3c6", x, y + 8, 6, h - 8);
  rect(c, "#bdba9d", x + w - 6, y + 8, 6, h - 8);
  rect(c, "#a69e83", x, y + h - 6, w, 6);
  rect(c, "#e1cd98", x + w / 2 - 10, y + h - 7, 20, 11);
  rect(c, "#6d8b89", x + 20, y - 1, 24, 5);
  rect(c, "#bdd6bd", x + 22, y, 9, 3);
  rect(c, "#bdd6bd", x + 33, y, 9, 3);
  if (kind === "home") {
    bed(
      c,
      x + 12,
      y + 17,
      ["#94aeb1", "#c89283", "#a9b885"][Math.floor(x) % 3],
    );
    shelf(c, x + w - 49, y + 13);
    table(c, x + w - 49, y + 48, 31, 20);
    rect(c, "#b5a276", x + 47, y + 30, 24, 35);
    rect(c, "#d0b78a", x + 50, y + 33, 18, 29);
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
    rect(c, "#8d9b6b", x + w / 2 - 16, y + 32, 32, 48);
    rect(c, "#c9ce9e", x + w / 2 - 13, y + 35, 26, 42);
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
  canvas.width = WIDTH;
  canvas.height = HEIGHT;
  const c = canvas.getContext("2d");
  c.imageSmoothingEnabled = false;
  rect(c, "#acc67d", 0, 0, WIDTH, HEIGHT);
  for (let y = 0; y < HEIGHT; y += 8)
    for (let x = 0; x < WIDTH; x += 8) {
      const k = (x * 17 + y * 31 + x * y) % 107;
      if (k < 22) rect(c, k % 2 ? "#b7cf88" : "#a3bd72", x + 2, y + 3, 3, 2);
      if (k === 4) {
        rect(c, "#8ead64", x + 1, y, 1, 3);
        rect(c, "#8ead64", x + 3, y + 1, 1, 2);
      }
    }
  // Riverbank and small wooden footbridge.
  for (let y = 0; y < HEIGHT; y += 16) {
    const edge = 915 + Math.round((Math.sin(y / 96) * 14) / 8) * 8;
    rect(c, "#dfcc9b", edge - 8, y, WIDTH - edge + 8, 16);
    rect(c, "#609398", edge, y, WIDTH - edge, 16);
    rect(c, "#79aeb0", edge + 5, y, WIDTH - edge - 5, 16);
    if (y % 32 === 0)
      for (let x = edge + 15; x < WIDTH; x += 37)
        rect(c, "#a4c9bf", x, y + 9, 17, 2);
  }
  const path = (x, y, w, h) => {
    rect(c, "#c9b880", x - 3, y - 3, w + 6, h + 6);
    rect(c, "#e2d09a", x, y, w, h);
    for (let yy = y + 4; yy < y + h; yy += 13)
      for (let xx = x + 5; xx < x + w; xx += 22)
        rect(c, "#d6c38d", xx, yy, 3, 2);
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
  house(c, 166, 58, 115, 91, "#a77b66");
  house(c, 370, 48, 108, 95, "#728993");
  house(c, 535, 48, 105, 95, "#ad8961");
  house(c, 745, 76, 111, 105, "#7f8d69");
  house(c, 404, 192, 210, 100, "#ab755c", "market");
  house(c, 76, 197, 160, 65, "#9c7860", "shed");
  for (let y = 329; y < 407; y += 22)
    for (let x = 83; x < 255; x += 24) {
      rect(c, "#90724b", x, y, 20, 17);
      rect(c, "#b08d5d", x, y + 2, 20, 4);
      rect(c, "#5f7e42", x + 7, y + 3, 4, 11);
      rect(c, "#71934a", x + 3, y + 3, 12, 5);
      rect(c, "#a9bb60", x + 7, y, 4, 6);
    }
  fence(c, 71, 321, 195, 89);
  fence(c, 72, 411, 195, 0);
  // Plaza stone tiles, fountain, benches and gardens.
  rect(c, "#91a269", 381, 336, 245, 130);
  rect(c, "#d2c7a3", 388, 340, 231, 121);
  for (let y = 343; y < 461; y += 16)
    for (let x = 390; x < 619; x += 18) {
      rect(c, (x + y) % 5 ? "#ddd4b4" : "#cbc3a5", x, y, 16, 14);
    }
  rect(c, "#8e9986", 486, 371, 53, 52);
  rect(c, "#eee1b9", 481, 376, 63, 42);
  rect(c, "#a9b6a7", 486, 380, 53, 34);
  rect(c, "#78a6a3", 490, 384, 45, 25);
  rect(c, "#b4d1c0", 495, 388, 34, 3);
  rect(c, "#d9dac1", 507, 377, 11, 27);
  rect(c, "#ece7c9", 503, 372, 19, 9);
  rect(c, "#b7d6c9", 507, 368, 11, 6);
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
  rect(c, "#d5c696", 741, 339, 105, 98);
  for (let y = 343; y < 434; y += 16)
    for (let x = 746; x < 843; x += 18) rect(c, "#e5d7ad", x, y, 14, 12);
  rect(c, "#718783", 767, 361, 47, 38);
  rect(c, "#b4b69d", 762, 366, 57, 26);
  rect(c, "#e5dfbf", 766, 362, 49, 8);
  rect(c, "#567e82", 774, 370, 32, 16);
  rect(c, "#8eb6b0", 779, 372, 22, 4);
  rect(c, "#7e6548", 758, 343, 5, 45);
  rect(c, "#7e6548", 818, 343, 5, 45);
  rect(c, "#93694f", 753, 333, 74, 13);
  rect(c, "#bf8e67", 758, 328, 64, 8);
  rect(c, "#6e5740", 790, 344, 3, 27);
  rect(c, "#a68b5c", 787, 367, 11, 8);
  bench(c, 765, 416);
  house(c, 158, 541, 113, 85, "#9b7c82");
  house(c, 367, 541, 111, 85, "#778d7f");
  house(c, 535, 541, 110, 85, "#b38468");
  house(c, 737, 536, 112, 88, "#8587a2");
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
export function layoutResidents(agents, events, day) {
  const slots = {};
  return agents.map((agent, index) => {
    const activity = presentationFor(agent, events, day);
    const slot = slots[activity.place] ?? 0;
    slots[activity.place] = slot + 1;
    return {
      id: agent.agentId,
      name: agent.displayName,
      index,
      activity,
      to: anchor(activity.place, slot),
    };
  });
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
    showNames = true,
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
    ctx.fillStyle = "#a4bf7a";
    ctx.fillRect(0, 0, size.w, size.h);
    ctx.translate(cam.x, cam.y);
    ctx.scale(cam.s, cam.s);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(background, 0, 0);
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
        ease = t * t * (3 - 2 * t);
      person.x = person.from.x + (person.to.x - person.from.x) * ease;
      person.y = person.from.y + (person.to.y - person.from.y) * ease;
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
        1.7,
        time - person.start < 850 ? time / 90 : 0,
      );
      if (showActions && (active || person.index % 5 === 0) && oldDay > 0) {
        rect(ctx, "#fffdf0", person.x - 10, person.y - 56, 22, 17);
        rect(ctx, "#fffdf0", person.x - 2, person.y - 39, 4, 4);
        ctx.font = "bold 13px monospace";
        ctx.fillStyle = "#5b6958";
        ctx.textAlign = "center";
        ctx.fillText(person.activity.icon, person.x + 1, person.y - 43);
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
