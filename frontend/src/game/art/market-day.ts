import type Phaser from "phaser";
import { layout } from "../world-layout";

// Temporary, non-interactive props, matching the town's cream striped awnings
// and warm wooden tables, along the plaza's southern footpath, clear of homes.
export function marketStalls(scene: Phaser.Scene) {
  const plaza = layout.places.plaza;
  const colors = [0xb76f5c, 0x769785, 0xc39c59, 0x7e97a8];
  return [
    [-90, -35],
    [-30, -35],
    [30, -35],
    [90, -35],
  ].map(([dx, dy], i) => {
    const x = plaza.x + dx,
      y = plaza.y + dy;
    const g = scene.add.graphics().setDepth(2).setName(`market-day-stall-${i}`);
    g.fillStyle(0x526454, 0.16).fillEllipse(x + 3, y + 17, 54, 17);
    g.fillStyle(0x7d7354)
      .fillRect(x - 19, y - 16, 3, 34)
      .fillRect(x + 16, y - 16, 3, 34);
    g.fillStyle(0xbfa175).fillRoundedRect(x - 23, y + 4, 46, 12, 2);
    g.fillStyle(0x8d7050).fillRect(x - 23, y + 14, 46, 3);
    g.fillStyle(0xf6edcf).fillTriangle(
      x - 26,
      y - 16,
      x,
      y - 29,
      x + 26,
      y - 16,
    );
    for (let stripe = 0; stripe < 6; stripe++) {
      g.fillStyle(stripe % 2 ? 0xf6edcf : colors[i]);
      g.fillRoundedRect(x - 27 + stripe * 9, y - 16, 9, 13, 2);
    }
    for (let n = 0; n < 4; n++) {
      g.fillStyle(i % 2 ? 0xa7b87c : 0xd6ac65);
      g.fillEllipse(x - 15 + n * 10, y + 5, 7, 5);
    }
    return g.setVisible(false);
  });
}
