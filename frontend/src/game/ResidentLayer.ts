import Phaser from "phaser";
import { canvasClick } from "./input";
import { traversedPath, pathDistance } from "./motion";
import { invQty, itemNames, type Inventory } from "../types";
import type { SceneReader, SceneEmit } from "./scene-types";
import { makeResidentTexture, type Facing } from "./art/residents";
import { workPose } from "./visual-state";
interface Person {
  container: Phaser.GameObjects.Container;
  sprite: Phaser.GameObjects.Image;
  ring: Phaser.GameObjects.Ellipse;
  label: Phaser.GameObjects.Text;
  activity: Phaser.GameObjects.Text;
  dot: Phaser.GameObjects.Arc;
  thought: Phaser.GameObjects.Text;
  index: number;
  tx: number;
  ty: number;
  serverPath: { x: number; y: number }[];
  waypoints: { x: number; y: number }[];
  speed: number;
  facing: Facing;
  sleeping: boolean;
}
const SHORT_ACTIONS: Record<string, string> = {
  harvest_veg: "采菜",
  gather_honey: "采蜜",
  harvest_flax: "收麻",
  weave: "织布",
  assemble: "木艺",
  cook: "烹饪",
  eat_soup: "用餐",
  honey_tea: "茶饮",
  delivery: "交货",
  gather: "采果",
  fish: "钓鱼",
  chop: "伐木",
  mine: "采矿",
  forage: "采药",
  grill: "烤鱼",
  forge: "打造",
  brew: "茶饮",
  picnic: "野餐",
  eat_fruit: "吃水果",
  eat_meal: "用餐",
  farm: "收获",
  craft: "木作",
  bake: "烘焙",
  work: "工作",
  rest: "回家",
  social: "交流",
  stroll: "散步",
  visit: "串门",
  daydream: "发呆",
  play: "玩耍",
  shop_browse: "逛集市",
  buy: "采购",
  sell: "售卖",
  contribute: "捐建",
  move: "前往",
};
export class ResidentLayer {
  people = new Map<string, Person>();
  route: Phaser.GameObjects.Graphics;
  private lastEvent: number | null = null;
  private reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)")
    .matches;
  constructor(
    private scene: Phaser.Scene,
    private state: SceneReader,
    private emit: SceneEmit,
    private dragged: () => boolean,
  ) {
    this.route = scene.add.graphics().setDepth(2);
    for (let i = 0; i < 12; i++)
      for (const d of ["front", "back", "left", "right"] as Facing[])
        for (let f = 0; f < 5; f++)
          scene.textures.addCanvas(
            `person-${i}-${d}-${f}`,
            makeResidentTexture(i, d, f),
          );
  }
  sync() {
    const { world, catalog } = this.state();
    Object.values(world.agents).forEach((a, i) => {
      let p = this.people.get(a.id);
      if (!p) {
        const shadow = this.scene.add.ellipse(0, 2, 23, 8, 0x345e48, 0.23);
        const ring = this.scene.add
          .ellipse(0, 2, 31, 13)
          .setStrokeStyle(2, 0xfff1b0)
          .setVisible(false);
        const sprite = this.scene.add
          .image(0, 0, `person-${i % 12}-front-0`)
          .setName("resident-avatar")
          .setDisplaySize(36, 48)
          .setOrigin(0.5, 0.895);
        const textStyle = {
          resolution: 2,
          fontFamily: '"PingFang SC", system-ui',
          fontSize: "11px",
          color: "#fff",
          backgroundColor: a.id === this.state().self ? "#346c5a" : "#586c59",
          padding: { x: 6, y: 3 },
        };
        const label = this.scene.add
          .text(0, 16, a.name, textStyle)

          .setOrigin(0.5);
        const activity = this.scene.add
          .text(0, -54, "", {
            resolution: 2,
            fontFamily: "system-ui",
            fontSize: "10px",
            color: "#3f5f50",
            backgroundColor: "#fffdf0",
            padding: { x: 6, y: 3 },
          })
          .setOrigin(0.5)

          .setAlpha(0.96)
          .setName("resident-activity");
        const thought = this.scene.add
          .text(0, -68, "…", {
            ...textStyle,
            color: "#3f5f50",
            backgroundColor: "#fffdf0",
          })
          .setName("resident-thought")
          .setOrigin(0.5)
          .setVisible(false);
        const dot = this.scene.add
          .circle(13, -34, 3, 0xcce8a7)
          .setStrokeStyle(1, 0x46745d);
        const container = this.scene.add.container(a.x, a.y, [
          shadow,
          ring,
          sprite,
          label,
          activity,
          thought,
          dot,
        ]);
        container.setName(`resident-${a.id}`);
        sprite
          .setInteractive({ useHandCursor: true })
          .on("pointerup", (pointer: Phaser.Input.Pointer) => {
            if (!this.dragged() && canvasClick(pointer, this.scene.game.canvas))
              this.emit("select", a.id);
          });
        sprite.on("pointerover", () => {
          label.setVisible(true);
          activity.setVisible(true);
        });
        sprite.on("pointerout", () => this.updateVisibility(a.id));
        p = {
          container,
          sprite,
          ring,
          label,
          activity,
          thought,
          dot,
          index: i,
          tx: a.x,
          ty: a.y,
          serverPath: a.path.map((n) => ({ ...n })),
          waypoints: [],
          speed: 20,
          facing: "front",
          sleeping: Boolean(a.sleeping),
        };
        container.setAlpha(a.sleeping ? 0 : 1);
        this.people.set(a.id, p);
      }
      if (Math.hypot(a.x - p.tx, a.y - p.ty) > 0.01) {
        const traversed = traversedPath({ x: p.tx, y: p.ty }, p.serverPath, a);
        if (traversed === null) {
          p.waypoints = [];
          p.container.setPosition(a.x, a.y);
        } else {
          p.waypoints.push(...traversed);
        }
        const interval = Math.max(0.1, catalog.tick_seconds);
        p.speed = Math.max(
          (catalog.movement_per_tick ?? 40) / interval,
          pathDistance(p.container, p.waypoints) / interval,
        );
        p.tx = a.x;
        p.ty = a.y;
      }
      p.sleeping = Boolean(a.sleeping);
      if (p.sprite.input) p.sprite.input.enabled = !p.sleeping;
      if (this.reducedMotion) p.container.setAlpha(p.sleeping ? 0 : 1);
      p.serverPath = a.path.map((n) => ({ ...n }));
      p.activity.setText(
        a.task
          ? a.path.length
            ? `↗ ${SHORT_ACTIONS[a.task.type] ?? "前往"}`
            : a.activity
          : a.mode === "rules"
            ? "规则托管"
            : a.mode === "plan"
              ? "按计划行动"
              : "",
      );
      p.ring.setVisible(a.id === this.state().selected);
      p.dot.setVisible(!a.npc && a.online);
      this.updateVisibility(a.id);
    });
    const events = this.state().events;
    if (this.lastEvent !== null) {
      for (const e of [...events]
        .reverse()
        .filter((e) => e.id > this.lastEvent!)) {
        const p = this.people.get(e.actor_id);
        if (!p || e.type === "blocked") continue;
        const after = e.details?.after as
          { cash?: number; inventory?: Inventory } | undefined;
        const before = e.details?.before as typeof after;
        let message =
          e.type === "leisure"
            ? (SHORT_ACTIONS[String(e.details?.kind)] ?? "生活片刻")
            : e.type === "social"
              ? e.details?.relationship_change
                ? `熟悉度 +${e.details.relationship_change}`
                : "交流完成"
              : e.type === "milestone"
                ? "★ 达成新徽章"
                : SHORT_ACTIONS[e.type]
                  ? `${SHORT_ACTIONS[e.type]}完成`
                  : "";
        if (after && before) {
          const cash = (after.cash ?? 0) - (before.cash ?? 0);
          if (cash) message = `${cash > 0 ? "+" : ""}${cash} 镇币`;
          else {
            const names = itemNames;
            const gains = Object.keys(names)
              .map((k) => ({
                k,
                n: invQty(after.inventory?.[k]) - invQty(before.inventory?.[k]),
              }))
              .filter((v) => v.n > 0);
            if (gains.length)
              message = gains.map((v) => `+${v.n} ${names[v.k]}`).join(" ");
          }
        }
        if (message) this.float(p, message, e.type === "milestone");
      }
    }
    this.lastEvent = Math.max(this.lastEvent ?? 0, ...events.map((e) => e.id));
  }
  private updateVisibility(id: string) {
    const p = this.people.get(id),
      a = this.state().world.agents[id];
    if (!p || !a) return;
    const selected = this.state().selected === id;
    p.label.setVisible(
      this.state().names || selected || id === this.state().self,
    );
    p.activity.setVisible(
      Boolean(p.activity.text) && (selected || id === this.state().self),
    );
  }
  private float(p: Person, message: string, badge = false) {
    const t = this.scene.add
      .text(p.container.x, p.container.y - (badge ? 82 : 52), message, {
        resolution: 2,
        fontFamily: "system-ui",
        fontSize: badge ? "13px" : "12px",
        fontStyle: "bold",
        color: badge ? "#67541f" : "#2d664d",
        backgroundColor: badge ? "#fff1b2" : "#fffdf0",
        padding: { x: 8, y: 5 },
      })
      .setOrigin(0.5)
      .setDepth(1800);
    this.scene.tweens.add({
      targets: t,
      y: t.y - 32,
      alpha: 0,
      delay: 1000,
      duration: 1700,
      onComplete: () => t.destroy(),
    });
  }
  update(time: number, delta: number) {
    const labelScale = Phaser.Math.Clamp(
      this.scene.scale.displayScale.x / this.scene.cameras.main.zoom,
      0.7,
      1.8,
    );
    for (const [id, p] of this.people) {
      p.container.setAlpha(
        Phaser.Math.Clamp(
          p.container.alpha + ((p.sleeping ? -1 : 1) * delta) / 400,
          0,
          1,
        ),
      );
      p.label.setScale(labelScale);
      p.activity.setScale(labelScale);
      p.thought.setScale(labelScale);
      let remaining = (Math.min(delta, 100) / 1000) * p.speed;
      const moving = p.waypoints.length > 0;
      while (p.waypoints.length && remaining > 0) {
        const node = p.waypoints[0],
          dx = node.x - p.container.x,
          dy = node.y - p.container.y,
          dist = Math.hypot(dx, dy);
        if (dist > 0.1)
          p.facing =
            Math.abs(dx) > Math.abs(dy)
              ? dx > 0
                ? "right"
                : "left"
              : dy > 0
                ? "front"
                : "back";
        if (dist <= remaining) {
          p.container.setPosition(node.x, node.y);
          p.waypoints.shift();
          remaining -= dist;
        } else {
          p.container.x += (dx / dist) * remaining;
          p.container.y += (dy / dist) * remaining;
          remaining = 0;
        }
      }
      p.container.setDepth(100 + p.container.y);
      const texture = `person-${p.index % 12}-${p.facing}-${moving ? 1 + (Math.floor(time / 130) % 4) : 0}`;
      if (p.sprite.texture.key !== texture) p.sprite.setTexture(texture);
      const agent = this.state().world.agents[id];
      // Both the server path and local interpolation must have finished.
      const task =
        !moving && !agent?.path.length ? agent?.task?.type : undefined;
      p.thought.setVisible(
        task === "daydream" &&
          !p.sleeping &&
          (this.reducedMotion ||
            Math.floor((time + p.index * 173) / 1800) % 3 === 0),
      );
      const pose = workPose(task, time + p.index * 173, this.reducedMotion);
      p.sprite
        .setPosition(pose.x, pose.y)
        .setAngle(pose.angle)
        .setDisplaySize(36, pose.height);
      if (!moving && !task && !this.reducedMotion)
        p.sprite.y = Math.sin(time / 1100 + p.index) * 0.35;
      if (id === this.state().selected)
        p.ring.setAlpha(0.7 + Math.sin(time / 350) * 0.25);
    }
    this.drawRoute(time);
  }
  private drawRoute(time: number) {
    this.route.clear();
    if (!this.state().routes) return;
    const { world, selected } = this.state(),
      p = this.people.get(selected),
      a = world.agents[selected];
    if (!p || !a) return;
    const nodes = [
      { x: p.container.x, y: p.container.y },
      ...p.waypoints,
      ...a.path,
    ];
    this.route.lineStyle(2, 0xfff8d3, 0.8);
    for (let i = 1; i < nodes.length; i++) {
      const a = nodes[i - 1],
        b = nodes[i],
        dx = b.x - a.x,
        dy = b.y - a.y,
        d = Math.hypot(dx, dy);
      for (let j = (time / 80) % 12; j < d; j += 12) {
        const end = Math.min(j + 5, d);
        this.route.lineBetween(
          a.x + (dx * j) / d,
          a.y + (dy * j) / d,
          a.x + (dx * end) / d,
          a.y + (dy * end) / d,
        );
      }
    }
    if (a.path.length) {
      const last = a.path[a.path.length - 1];
      this.route.lineStyle(2, 0xfff8d3, 0.8);
      this.route.strokeCircle(last.x, last.y, 6 + Math.sin(time / 300) * 1.5);
    }
  }
}
