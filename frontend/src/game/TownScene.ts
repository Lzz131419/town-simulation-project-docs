import Phaser from "phaser";
import { canvasClick } from "./input";
import { layout, type CameraArea } from "./world-layout";
import { makeMapTexture, SCENE_BOUNDS, BUILDINGS } from "./art/map";
import { ResidentLayer } from "./ResidentLayer";
import { Atmosphere } from "./Atmosphere";
import type { SceneReader, SceneEmit } from "./scene-types";
export interface TownSceneHandle extends Phaser.Scene {
  focusRegion: (id: string) => void;
  zoomBy: (delta: number) => void;
  fit: number;
  reset: () => void;
  sync: () => void;
  focusAt: (x: number, y: number) => void;
}
export function makeTownScene(
  state: SceneReader,
  emit: SceneEmit,
  onReady: (scene: TownSceneHandle) => void,
  onViewport: (area: CameraArea) => void,
) {
  return class TownScene extends Phaser.Scene {
    private residents!: ResidentLayer;
    private atmosphere!: Atmosphere;
    private drag = false;
    private lastPointer = { x: 0, y: 0 };
    private down = { x: 0, y: 0 };
    private ready = false;
    private manualCamera = false;
    private previousFollow = false;
    private lastViewport = 0;
    private tags = new Map<string, Phaser.GameObjects.Text>();
    fit = 1;
    private fitArea: CameraArea = layout.overview;
    private resizeAnchor: { x: number; y: number } | null = null;
    create() {
      const b = SCENE_BOUNDS;
      this.textures.addCanvas("town-hd", makeMapTexture());
      this.add
        .image(b.x + b.width / 2, b.y + b.height / 2, "town-hd")
        .setDisplaySize(b.width, b.height);
      this.cameras.main.setBackgroundColor("#a4c88d");
      this.cameras.main.setBounds(b.x, b.y, b.width, b.height);
      for (const [id, place] of Object.entries(state().catalog.places)) {
        const building = BUILDINGS.find((b) => b.id === id);
        const x = building ? building.x + building.w / 2 : place.x,
          y = building ? building.y + building.h + 14 : place.y + 7;
        const tag = this.add
          .text(x, y, place.name, {
            resolution: 2,
            fontFamily: '"PingFang SC", system-ui',
            fontSize: "11px",
            fontStyle: "bold",
            color: "#355c49",
            backgroundColor: "#fffdf1ed",
            padding: { x: 7, y: 4 },
          })
          .setOrigin(0.5)

          .setDepth(850);
        const glow = this.add.graphics().setDepth(3).setVisible(false);
        if (building)
          glow
            .lineStyle(2, 0xfff1b0)
            .strokeRoundedRect(
              building.x - 2,
              building.y - 2,
              building.w + 4,
              building.h + 4,
              5,
            );
        else
          glow.lineStyle(2, 0xfff1b0).strokeEllipse(place.x, place.y, 50, 20);
        const zone = this.add
          .zone(
            building ? building.x + building.w / 2 : place.x,
            building ? building.y + building.h / 2 : place.y,
            building?.w ?? 65,
            building?.h ?? 30,
          )
          .setDepth(4)
          .setInteractive({ useHandCursor: true });
        const over = () => {
          glow.setVisible(true);
          tag.setBackgroundColor("#fff0b4");
        };
        const out = () => {
          glow.setVisible(false);
          tag.setBackgroundColor("#fffdf1");
        };
        zone
          .on("pointerover", over)
          .on("pointerout", out)
          .on("pointerup", (p: Phaser.Input.Pointer) => {
            if (!this.drag && canvasClick(p, this.game.canvas))
              emit("place", id);
          });
        tag
          .setInteractive({ useHandCursor: true })
          .on("pointerover", over)
          .on("pointerout", out)
          .on("pointerup", (p: Phaser.Input.Pointer) => {
            if (!this.drag && canvasClick(p, this.game.canvas))
              emit("place", id);
          });
        this.tags.set(id, tag);
      }
      this.residents = new ResidentLayer(this, state, emit, () => this.drag);
      this.atmosphere = new Atmosphere(this, state);
      this.input.on("pointerdown", (p: Phaser.Input.Pointer) => {
        this.drag = false;
        this.down = { x: p.x, y: p.y };
        this.lastPointer = { x: p.x, y: p.y };
      });
      this.input.on("pointermove", (p: Phaser.Input.Pointer) => {
        if (!p.isDown) return;
        if (Math.abs(p.x - this.down.x) + Math.abs(p.y - this.down.y) > 6)
          this.drag = true;
        if (this.drag) {
          this.resizeAnchor = null;
          this.manualCamera = true;
          emit("freeCamera", "");
          this.cameras.main.scrollX -=
            (p.x - this.lastPointer.x) / this.cameras.main.zoom;
          this.cameras.main.scrollY -=
            (p.y - this.lastPointer.y) / this.cameras.main.zoom;
        }
        this.lastPointer = { x: p.x, y: p.y };
      });
      this.input.on(
        "wheel",
        (
          _p: Phaser.Input.Pointer,
          _objects: unknown,
          _dx: number,
          dy: number,
        ) => {
          this.zoomBy(this.cameras.main.zoom * (dy < 0 ? 0.1 : -0.1));
        },
      );
      this.scale.on("resize", () => {
        const camera = this.cameras.main;
        this.resizeAnchor ??= {
          x: camera.worldView.centerX,
          y: camera.worldView.centerY,
        };
        const nextFit = Math.min(
          this.scale.width / this.fitArea.width,
          this.scale.height / this.fitArea.height,
        );
        const zoom = (camera.zoom * nextFit) / this.fit;
        this.fit = nextFit;
        camera.setSize(this.scale.width, this.scale.height);
        camera.setZoom(zoom);
        camera.panEffect.reset();
        camera.centerOn(this.resizeAnchor.x, this.resizeAnchor.y);
      });
      this.focusRegion("town");
      this.ready = true;
      this.sync();
      onReady(this);
    }
    private frame(area: CameraArea) {
      this.fitArea = area;
      this.resizeAnchor = { x: area.x, y: area.y };
      this.cameras.main.panEffect.reset();
      this.fit = Math.min(
        this.scale.width / area.width,
        this.scale.height / area.height,
      );
      this.cameras.main.setZoom(this.fit);
      this.cameras.main.centerOn(area.x, area.y);
      this.manualCamera = true;
    }
    reset() {
      this.frame(layout.overview);
    }
    focusRegion(id: string) {
      this.frame(layout.districts.find((d) => d.id === id) ?? layout.overview);
    }
    zoomBy(delta: number) {
      this.resizeAnchor = null;
      emit("freeCamera", "");
      this.cameras.main.setZoom(
        Phaser.Math.Clamp(
          this.cameras.main.zoom + delta,
          this.fit * 0.75,
          this.fit * 2.8,
        ),
      );
    }
    focusAt(x: number, y: number) {
      this.resizeAnchor = { x, y };
      this.manualCamera = true;
      this.cameras.main.pan(x, y, 350, "Sine.easeInOut");
    }
    sync() {
      if (!this.ready) return;
      this.residents.sync();
      for (const [id, tag] of this.tags) {
        const place = state().catalog.places[id];
        const n = Object.values(state().world.agents).filter(
          (a) => Math.hypot(a.x - place.x, a.y - place.y) < 65,
        ).length;
        tag.setText(place.name + (n ? ` · ${n}` : ""));
      }
    }
    update(time: number, delta: number) {
      if (!this.ready) return;
      if (time - this.lastViewport > 120) {
        const v = this.cameras.main.worldView;
        onViewport({ x: v.x, y: v.y, width: v.width, height: v.height });
        this.lastViewport = time;
      }
      const labelScale = Phaser.Math.Clamp(
        this.scale.displayScale.x / this.cameras.main.zoom,
        0.7,
        1.8,
      );
      for (const tag of this.tags.values()) tag.setScale(labelScale);
      this.residents.update(time, delta);
      this.atmosphere.update(time);
      const follow = state().follow;
      if (follow !== this.previousFollow) {
        this.manualCamera = false;
        this.previousFollow = follow;
      }
      if (follow && !this.manualCamera) {
        this.resizeAnchor = null;
        const p = this.residents.people.get(state().selected);
        if (p) {
          const cam = this.cameras.main;
          const blend = 1 - Math.exp(-delta / 220);
          cam.centerOn(
            Phaser.Math.Linear(cam.midPoint.x, p.container.x, blend),
            Phaser.Math.Linear(cam.midPoint.y, p.container.y, blend),
          );
        }
      }
    }
  };
}
