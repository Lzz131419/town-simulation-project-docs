import Phaser from "phaser";
import type { SceneReader } from "./scene-types";
import { layout, onBridge } from "./world-layout";
import { daylight } from "./lighting";
import { LAMP_POSTS } from "./art/lighting-props";
import { SCENE_BOUNDS } from "./art/terrain";
export class Atmosphere {
  private lastDraw = -Infinity;
  private lastAmbience: boolean | undefined;
  private water: Phaser.GameObjects.Graphics;
  private overlay: Phaser.GameObjects.Rectangle;
  private sunset: Phaser.GameObjects.Rectangle;
  private lamps: Phaser.GameObjects.Image[] = [];
  private motes: Phaser.GameObjects.Arc[] = [];
  private reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)")
    .matches;
  private lightState = { night: 0, warmth: 0, lamps: 0 };
  constructor(
    scene: Phaser.Scene,
    private state: SceneReader,
  ) {
    const b = SCENE_BOUNDS;
    this.water = scene.add.graphics().setDepth(1);
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
      ["home", "bakery", "teahouse", "kitchen"].includes(b.kind),
    )) {
      this.lamps.push(
        scene.add
          .image(b.x + b.w * 0.5, b.y + b.h * 0.42, "town-lamp-glow")
          .setDisplaySize(b.w * 0.85, b.h * 0.8)
          .setDepth(949)
          .setAlpha(0),
      );
    }
    for (let i = 0; i < 24; i++)
      this.motes.push(
        scene.add
          .circle(0, 0, 1.1, i % 2 ? 0xffe9a0 : 0xe5f0c2, 0.6)
          .setDepth(960),
      );
  }
  update(time: number) {
    const { ambience, world } = this.state();
    if (ambience === this.lastAmbience && time - this.lastDraw < 1000 / 24)
      return;
    const first = this.lastAmbience === undefined;
    const elapsed = Math.min(100, time - this.lastDraw);
    this.lastDraw = time;
    this.lastAmbience = ambience;
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
    this.motes.forEach((m, i) => {
      m.setVisible(!this.reducedMotion);
      // A handful of fireflies gather at meadow and flower beds instead of covering every room.
      const base = i < 12 ? { x: 470, y: 880 } : { x: 1660, y: 150 };
      m.setPosition(
        base.x + Math.sin(motion / (3000 + i * 75) + i) * 85,
        base.y + Math.cos(motion / (2400 + i * 40) + i * 3) * 45,
      );
      m.setAlpha(
        this.lightState.lamps * (0.25 + Math.sin(motion / 1000 + i) ** 2 * 0.4),
      );
    });
  }
}
