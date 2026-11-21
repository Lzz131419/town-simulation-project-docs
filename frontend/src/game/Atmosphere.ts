import type Phaser from "phaser";
import type { SceneReader } from "./scene-types";
import { layout, onBridge } from "./world-layout";
import { daylight } from "./lighting";
import { LAMP_POSTS } from "./art/lighting-props";
import { SCENE_BOUNDS } from "./art/terrain";
import { isMarketDay } from "./market-day";
import { marketStalls } from "./art/market-day";
import { weatherVisuals } from "./visual-state";
export class Atmosphere {
  private homeLights: {
    glow: Phaser.GameObjects.Image;
    windows: Phaser.GameObjects.Graphics;
  }[] = [];
  private stalls: Phaser.GameObjects.Graphics[];
  private lastDraw = -Infinity;
  private lastAmbience: boolean | undefined;
  private lastWeather: string | undefined;
  private lastSeason: string | undefined;
  private water: Phaser.GameObjects.Graphics;
  private overlay: Phaser.GameObjects.Rectangle;
  private sunset: Phaser.GameObjects.Rectangle;
  private precipitation: Phaser.GameObjects.Graphics;
  private weatherShade: Phaser.GameObjects.Rectangle;
  private fog: Phaser.GameObjects.Image;
  private lamps: Phaser.GameObjects.Image[] = [];
  private motes: Phaser.GameObjects.Arc[] = [];
  private reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)")
    .matches;
  private lightState = { night: 0, warmth: 0, lamps: 0 };
  constructor(
    scene: Phaser.Scene,
    private state: SceneReader,
  ) {
    this.stalls = marketStalls(scene);
    const b = SCENE_BOUNDS;
    this.water = scene.add.graphics().setDepth(1).setName("water-motion");
    this.precipitation = scene.add
      .graphics()
      .setDepth(3002)
      .setName("weather-precipitation");
    this.weatherShade = scene.add
      .rectangle(
        b.x + b.width / 2,
        b.y + b.height / 2,
        b.width,
        b.height,
        0x24364d,
      )
      .setDepth(3000)
      .setName("weather-shade")
      .setAlpha(0);
    const mist = document.createElement("canvas");
    mist.width = mist.height = 256;
    const mistContext = mist.getContext("2d")!;
    const vignette = mistContext.createRadialGradient(
      128,
      128,
      38,
      128,
      128,
      175,
    );
    vignette.addColorStop(0, "#46576200");
    vignette.addColorStop(0.6, "#46576216");
    vignette.addColorStop(1, "#34495688");
    mistContext.fillStyle = vignette;
    mistContext.fillRect(0, 0, 256, 256);
    if (!scene.textures.exists("town-weather-fog"))
      scene.textures.addCanvas("town-weather-fog", mist);
    this.fog = scene.add
      .image(b.x + b.width / 2, b.y + b.height / 2, "town-weather-fog")
      .setDisplaySize(b.width, b.height)
      .setDepth(3001)
      .setName("weather-fog")
      .setVisible(false);
    this.overlay = scene.add
      .rectangle(
        b.x + b.width / 2,
        b.y + b.height / 2,
        b.width,
        b.height,
        0x142f53,
        1,
      )
      .setDepth(900)
      .setAlpha(0);
    this.sunset = scene.add
      .rectangle(
        b.x + b.width / 2,
        b.y + b.height / 2,
        b.width,
        b.height,
        0xf0ad58,
        1,
      )
      .setDepth(901)
      .setAlpha(0);
    const glow = document.createElement("canvas");
    glow.width = 128;
    glow.height = 128;
    const c = glow.getContext("2d")!,
      g = c.createRadialGradient(64, 64, 0, 64, 64, 64);
    g.addColorStop(0, "#fff2b8a0");
    g.addColorStop(0.12, "#ffdd8880");
    g.addColorStop(0.4, "#f7b95722");
    g.addColorStop(1, "#f7b95700");
    c.fillStyle = g;
    c.fillRect(0, 0, 128, 128);
    if (!scene.textures.exists("town-lamp-glow"))
      scene.textures.addCanvas("town-lamp-glow", glow);
    for (const [x, y] of LAMP_POSTS) {
      this.lamps.push(
        scene.add
          .image(x, y - 27, "town-lamp-glow")
          .setDisplaySize(74, 74)
          .setDepth(950)
          .setAlpha(0),
      );
      this.lamps.push(
        scene.add
          .image(x + 3, y, "town-lamp-glow")
          .setDisplaySize(52, 28)
          .setDepth(949)
          .setAlpha(0),
      );
    }
    for (const b of layout.buildings.filter((b) =>
      ["bakery", "teahouse", "kitchen"].includes(b.kind),
    )) {
      this.lamps.push(
        scene.add
          .image(b.x + b.w * 0.5, b.y + b.h * 0.42, "town-lamp-glow")
          .setDisplaySize(b.w * 0.85, b.h * 0.8)
          .setDepth(949)
          .setAlpha(0),
      );
    }
    // All agents share the server home destination. Rotate occupied houses by
    // game night, lighting one house per sleeping resident (up to seven).
    for (const b of layout.buildings.filter((b) => b.kind === "home")) {
      const glow = scene.add
        .image(b.x + b.w / 2, b.y + 12, "town-lamp-glow")
        .setDisplaySize(b.w * 1.3, b.h * 0.95)
        .setDepth(949)
        .setAlpha(0);
      const windows = scene.add
        .graphics()
        .setDepth(950)
        .setName(`sleep-windows-${this.homeLights.length}`)
        .setAlpha(0);
      for (let x = b.x + 19; x < b.x + b.w - 12; x += 43) {
        windows
          .fillStyle(0xffd77e, 0.95)
          .fillRoundedRect(x + 1, b.y - 2, 20, 6, 1);
        windows
          .lineStyle(1, 0x916b40, 0.8)
          .lineBetween(x + 11, b.y - 2, x + 11, b.y + 4);
        windows
          .fillStyle(0xffd77e, 0.12)
          .fillTriangle(x, b.y + 6, x + 22, b.y + 6, x + 38, b.y + 36);
      }
      this.homeLights.push({ glow, windows });
    }
    for (let i = 0; i < 48; i++)
      this.motes.push(
        scene.add
          .circle(0, 0, 1.1, i % 2 ? 0xffe9a0 : 0xe5f0c2, 0.6)
          .setDepth(960),
      );
    // Apply the current snapshot immediately, including a rainy first frame.
    this.update(0);
  }
  update(time: number) {
    const { ambience, world } = this.state();
    this.stalls.forEach((stall) => stall.setVisible(isMarketDay(world)));
    const houseAlpha = ambience ? daylight(world.tick).lamps : 0;
    this.homeLights.forEach(({ glow, windows }, i) => {
      const home = world.homes?.find((h) => h.id === `home-${i + 1}`);
      const occupied =
        Boolean(home?.owner_id) &&
        Object.values(world.agents).some(
          (a) => a.home_id === home?.id && Boolean(a.sleeping),
        );
      const alpha = occupied ? houseAlpha : 0;
      glow.setAlpha(alpha);
      windows.setAlpha(alpha);
    });
    if (
      ambience === this.lastAmbience &&
      world.weather === this.lastWeather &&
      world.season === this.lastSeason &&
      time - this.lastDraw < 1000 / 24
    )
      return;
    const first = this.lastAmbience === undefined;
    const elapsed = Math.min(100, time - this.lastDraw);
    this.lastDraw = time;
    this.lastAmbience = ambience;
    this.lastWeather = world.weather;
    this.lastSeason = world.season;
    const weather = weatherVisuals(world, ambience, this.reducedMotion);
    this.weatherShade.setAlpha(weather.shade);
    this.fog.setVisible(weather.fog);
    this.precipitation.clear();
    const target = ambience
      ? daylight(world.tick)
      : { night: 0, warmth: 0, lamps: 0 };
    const blend = first || !ambience ? 1 : 1 - Math.exp(-elapsed / 600);
    for (const key of ["night", "warmth", "lamps"] as const)
      this.lightState[key] += (target[key] - this.lightState[key]) * blend;
    this.overlay.setAlpha(this.lightState.night);
    this.sunset.setAlpha(this.lightState.warmth);
    this.lamps.forEach((l) => l.setAlpha(this.lightState.lamps));
    this.water.clear();
    if (!ambience) {
      this.motes.forEach((m) => m.setVisible(false));
      return;
    }
    const motion = this.reducedMotion ? 0 : time;
    const bounds = SCENE_BOUNDS;
    // Seeded positions give continuous wrapping motion without per-frame random
    // flicker. Reduced motion freezes the pattern and halves its density.
    for (let i = 0; i < weather.count; i++) {
      const snow = weather.precipitation === "snow";
      const fall =
        motion * (snow ? 0.028 : world.weather === "storm" ? 0.66 : 0.46);
      const y = bounds.y + ((i * 127.73 + fall) % bounds.height);
      const x =
        bounds.x +
        ((i * 293.27 + fall * (snow ? 0.1 : weather.slant / weather.length)) %
          bounds.width);
      if (snow) {
        this.precipitation.fillStyle(
          0xffffff,
          this.reducedMotion ? 0.35 : 0.72,
        );
        this.precipitation.fillCircle(
          x + Math.sin(motion / 1900 + i) * 5,
          y,
          1.4 + (i % 3) * 0.4,
        );
      } else {
        this.precipitation.lineStyle(
          1,
          0xd9ecf4,
          this.reducedMotion ? 0.2 : 0.46,
        );
        this.precipitation.lineBetween(
          x,
          y,
          x + weather.slant,
          y + weather.length,
        );
      }
    }
    // Fine current strokes follow the whole river and stay off bridges and the moored boat.
    for (let i = 0; i < 62; i++) {
      const x = layout.river.x + 6 + ((i * 17) % (layout.river.width - 24));
      const y = bounds.y + ((i * 43 + motion / 85) % bounds.height);
      if (onBridge(x, y) || (y > 1108 && y < 1205)) continue;
      const alpha = 0.12 + Math.sin(motion / 1300 + i) ** 2 * 0.22;
      this.water.lineStyle(0.7, 0xe4f4dc, alpha);
      this.water.lineBetween(
        x,
        y,
        x + 6 + Math.sin(motion / 900 + i) * 3,
        y - 1,
      );
    }
    for (let i = 0; i < 3; i++) {
      const radius = 3 + ((motion / 210 + i * 5) % 14);
      this.water.lineStyle(0.7, 0xf2fcf3, (1 - radius / 18) * 0.6);
      this.water.strokeEllipse(512, 393, radius * 2, radius);
    }
    for (let i = 0; i < weather.ripples; i++) {
      const x = layout.river.x + 12 + ((i * 37.13) % (layout.river.width - 30));
      const y = bounds.y + ((i * 97.37) % bounds.height);
      if (onBridge(x, y) || (y > 1108 && y < 1205)) continue;
      const phase = (motion / 950 + i * 0.37) % 1;
      const radius = 1 + phase * 6;
      this.water.lineStyle(0.8, 0xe4f3f5, (1 - phase) * 0.5);
      this.water.strokeEllipse(x, y, radius * 2, radius);
    }
    this.motes.forEach((m, i) => {
      m.setVisible(
        i < weather.motes / (this.reducedMotion ? 2 : 1) &&
          (!this.reducedMotion || weather.fog),
      );
      // A handful of fireflies gather at meadow and flower beds instead of covering every room.
      const base =
        i < 24
          ? i < 12
            ? { x: 470, y: 880 }
            : { x: 1660, y: 150 }
          : {
              x: bounds.x + ((i * 163) % bounds.width),
              y: bounds.y + ((i * 89) % bounds.height),
            };
      m.setPosition(
        base.x + Math.sin(motion / (3000 + i * 75) + i) * 85,
        base.y + Math.cos(motion / (2400 + i * 40) + i * 3) * 45,
      );
      m.setAlpha(
        (weather.fog ? 0.28 : this.lightState.lamps) *
          (0.25 + Math.sin(motion / 1000 + i) ** 2 * 0.4),
      );
    });
  }
}
