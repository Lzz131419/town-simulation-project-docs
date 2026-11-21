import Phaser from "phaser";
import { BUILDINGS } from "./buildings";
import type { SceneReader, SceneEmit } from "../scene-types";
import { canvasClick } from "../input";

// Separate overlays preserve the baked cutaway interiors and seasonal texture.
export class HomeLayer {
  private entries: {
    b: (typeof BUILDINGS)[number];
    id: string;
    level: number;
    flashUntil: number;
    art: Phaser.GameObjects.Graphics;
    flash: Phaser.GameObjects.Graphics;
    tag: Phaser.GameObjects.Text;
  }[];
  constructor(
    private scene: Phaser.Scene,
    private state: SceneReader,
    emit: SceneEmit,
    dragging: () => boolean,
  ) {
    this.entries = BUILDINGS.filter((b) => b.kind === "home").map((b) => ({
      b,
      id: b.id.replace("house-", "home-"),
      level: 0,
      flashUntil: 0,
      art: this.scene.add
        .graphics()
        .setDepth(0.3)
        .setName(`home-upgrade-${b.id}`),
      flash: this.scene.add
        .graphics()
        .setDepth(4)
        .setName(`home-flash-${b.id}`),
      tag: this.scene.add
        .text(b.x + b.w / 2, b.y + b.h + 25, "", {
          fontFamily: '"PingFang SC", system-ui',
          fontSize: "11px",
          color: "#355c49",
          backgroundColor: "#fffdf1ed",
          padding: { x: 6, y: 3 },
          resolution: 2,
        })
        .setOrigin(0.5)
        .setDepth(850),
    }));
    for (const entry of this.entries) {
      const { b, tag } = entry;
      const select = (p: Phaser.Input.Pointer) => {
        if (dragging() || !canvasClick(p, scene.game.canvas)) return;
        const home = this.state().world.homes?.find((h) => h.id === entry.id);
        if (home?.owner_id) emit("select", home.owner_id);
        else emit("place", "home");
      };
      scene.add
        .zone(b.x + b.w / 2, b.y + b.h / 2, b.w, b.h)
        .setDepth(4)
        .setInteractive({ useHandCursor: true })
        .on("pointerup", select);
      tag.setInteractive({ useHandCursor: true }).on("pointerup", select);
    }
  }
  update(time: number) {
    const { world, names } = this.state();
    for (const entry of this.entries) {
      const home = world.homes?.find((h) => h.id === entry.id);
      const level = home?.level ?? 1;
      const owner = home?.owner_id ? world.agents[home.owner_id] : undefined;
      entry.tag
        .setText(`${owner ? owner.name + "的家" : "待认领住宅"} · ${level} 级`)
        .setVisible(names);
      entry.tag.setScale(
        Phaser.Math.Clamp(
          this.scene.scale.displayScale.x / this.scene.cameras.main.zoom,
          0.7,
          1.8,
        ),
      );
      const { x, y, w, h } = entry.b;
      if (level !== entry.level) {
        if (entry.level && level > entry.level) entry.flashUntil = time + 900;
        entry.level = level;
        const g = entry.art.clear();
        if (level >= 2) {
          // Warm brick wall caps and a larger masonry chimney.
          g.fillStyle(0xb77f64)
            .fillRect(x, y + 10, 6, h - 14)
            .fillRect(x + w - 6, y + 10, 6, h - 14);
          g.lineStyle(1, 0xefd5b7, 0.8);
          for (let yy = y + 14; yy < y + h - 4; yy += 7) {
            g.lineBetween(x, yy, x + 6, yy).lineBetween(
              x + w - 6,
              yy,
              x + w,
              yy,
            );
          }
          g.fillStyle(0xb68169).fillRoundedRect(
            x + w * 0.72 - 2,
            y - 35,
            12,
            24,
            1,
          );
          g.fillStyle(0x6e5145).fillRect(x + w * 0.72 - 4, y - 38, 16, 5);
          g.lineStyle(1, 0xf0cfaa, 0.7);
          for (let yy = y - 30; yy < y - 10; yy += 6)
            g.lineBetween(x + w * 0.72 - 2, yy, x + w * 0.72 + 10, yy);
        }
        if (level >= 3) {
          g.lineStyle(5, 0x785e48)
            .lineBetween(x - 12, y + 11, x + w / 2, y - 19)
            .lineBetween(x + w / 2, y - 19, x + w + 12, y + 11);
          g.lineStyle(1, 0xefcf93)
            .lineBetween(x - 12, y + 9, x + w / 2, y - 21)
            .lineBetween(x + w / 2, y - 21, x + w + 12, y + 9);
          // Garden fence leaves a wide opening in front of the door.
          g.lineStyle(2, 0xe8dbb7);
          for (const [left, right] of [
            [x - 10, x + w / 2 - 15],
            [x + w / 2 + 15, x + w + 10],
          ]) {
            g.lineBetween(left, y + h + 12, right, y + h + 12);
            for (let xx = left; xx <= right; xx += 9)
              g.lineBetween(xx, y + h + 6, xx, y + h + 18);
          }
          for (const xx of [x + 13, x + w - 23]) {
            g.fillStyle(0x927354).fillRoundedRect(xx, y + h - 2, 18, 10, 2);
            for (let i = 0; i < 3; i++) {
              g.fillStyle(0x66935e).fillCircle(xx + 4 + i * 5, y + h, 4);
              g.fillStyle(i % 2 ? 0xf7da86 : 0xeaa5aa).fillCircle(
                xx + 4 + i * 5,
                y + h - 3,
                2.5,
              );
            }
          }
        }
      }
      const alpha = Math.max(0, (entry.flashUntil - time) / 900);
      entry.flash.clear().setAlpha(alpha);
      if (alpha) {
        entry.flash
          .lineStyle(3, 0xffeb9a)
          .strokeRoundedRect(x - 8, y - 8, w + 16, h + 16, 7);
        for (let i = 0; i < 7; i++)
          entry.flash
            .fillStyle(0xffedaf)
            .fillCircle(x + (i * w) / 6, y + h + (1 - alpha) * 12, 3 * alpha);
      }
    }
  }
}
