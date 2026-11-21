import Phaser from "phaser";
import { makeTownScene, type TownSceneHandle } from "../../src/game/TownScene";
import type { SceneState } from "../../src/game/scene-types";
import { BUILDINGS } from "../../src/game/art/buildings";
import { SCENE_BOUNDS } from "../../src/game/art/map";

// Standalone SceneReader fixture: no application login, API calls or saved data.
const state: SceneState = {
  world: {
    homes: BUILDINGS.filter((b) => b.kind === "home").map((b, i) => ({
      id: `home-${i + 1}`,
      x: b.x + b.w / 2,
      y: b.y + b.h / 2,
      level: 1,
      owner_id: i === 0 ? "worker" : null,
    })),
    schema_version: 1,
    tick: 24,
    weather: "rain",
    season: "summer",
    agents: {
      worker: {
        home_id: "home-1",
        id: "worker",
        name: "测试居民",
        npc: true,
        x: 180,
        y: 370,
        cash: 0,
        energy: 100,
        hunger: 0,
        inventory: {},
        mode: "manual",
        path: [],
        task: { type: "gather" },
        activity: "采果",
        completed: 0,
        earned: 0,
        relations: {},
        last_outcome: "",
        online: true,
      },
    },
    market: {},
    treasury: 0,
    orders: [],
    project: {
      name: "",
      wood: 0,
      wood_target: 0,
      cash: 0,
      cash_target: 0,
      completed: false,
      contributors: {},
    },
    activity_goal: { name: "", trades: 0, target: 0 },
  },
  catalog: { items: {}, places: {}, actions: {}, members: [], tick_seconds: 1 },
  self: "worker",
  selected: "",
  names: false,
  routes: false,
  ambience: true,
  follow: false,
  events: [],
};

let scene: TownSceneHandle;
function snapshot() {
  const graphics = (name: string) =>
    scene.children.getByName(name) as Phaser.GameObjects.Graphics;
  const worker = scene.children.getByName(
    "resident-worker",
  ) as Phaser.GameObjects.Container;
  const sprite = worker.getByName(
    "resident-avatar",
  ) as Phaser.GameObjects.Image;
  const map = scene.textures.get("town-hd") as Phaser.Textures.CanvasTexture;
  // Sample a leaf in the first tree, away from branches and the background.
  const leaf = Array.from(
    map.context.getImageData(
      (36 - SCENE_BOUNDS.x) * 3,
      (62 - SCENE_BOUNDS.y) * 3,
      1,
      1,
    ).data,
  );
  return {
    homeArt: [1, 2, 3].map((i) => [
      ...graphics(`home-upgrade-house-${i}`).commandBuffer,
    ]),
    homeFlash: graphics("home-flash-house-2").alpha,
    thought: (worker.getByName("resident-thought") as Phaser.GameObjects.Text)
      .visible,
    activity: (worker.getByName("resident-activity") as Phaser.GameObjects.Text)
      .text,
    sleepingAlpha: worker.alpha,
    sleepingInteractive: sprite.input?.enabled,
    homeLights: [0, 1, 2, 3, 4, 5, 6].map(
      (i) => graphics(`sleep-windows-${i}`).alpha,
    ),
    stalls: [0, 1, 2, 3].map((i) => graphics(`market-day-stall-${i}`).visible),
    rain: [...graphics("weather-precipitation").commandBuffer],
    water: [...graphics("water-motion").commandBuffer],
    fog: (scene.children.getByName("weather-fog") as Phaser.GameObjects.Image)
      .visible,
    shade: (
      scene.children.getByName("weather-shade") as Phaser.GameObjects.Rectangle
    ).alpha,
    roof: graphics("roof-snow").visible,
    leaf,
    textures: scene.textures.getTextureKeys().length,
    avatar: {
      x: sprite.x,
      y: sprite.y,
      angle: sprite.angle,
      height: sprite.displayHeight,
      texture: sprite.texture.key,
    },
  };
}

const Scene = makeTownScene(
  () => state,
  () => {},
  (ready) => {
    scene = ready;
    scene.scene.pause();
    (window as unknown as { visuals: unknown }).visuals = {
      snapshot,
      focusHomes() {
        scene.cameras.main.panEffect.reset();
        scene.cameras.main.setZoom(1.65);
        scene.cameras.main.centerOn(440, 200);
      },
      focusMarket() {
        scene.cameras.main.panEffect.reset();
        scene.cameras.main.setZoom(2);
        scene.cameras.main.centerOn(503, 500);
      },
      step(options: {
        homes?: SceneState["world"]["homes"];
        names?: boolean;
        home_id?: string | null;
        sleeping?: SceneState["world"]["agents"][string]["sleeping"];
        tick?: number;
        market_day?: SceneState["world"]["market_day"];
        weather?: SceneState["world"]["weather"];
        season?: SceneState["world"]["season"];
        ambience?: boolean;
        task?: string | null;
        activity?: string;
        path?: { x: number; y: number }[];
        position?: { x: number; y: number };
        time?: number;
      }) {
        const {
          weather,
          season,
          ambience,
          task,
          path,
          position,
          time = 1000,
        } = options;
        if (options.homes !== undefined) state.world.homes = options.homes;
        if (options.names !== undefined) state.names = options.names;
        if (options.home_id !== undefined)
          state.world.agents.worker.home_id = options.home_id;
        if (options.tick !== undefined) state.world.tick = options.tick;
        if (options.market_day !== undefined)
          state.world.market_day = options.market_day;
        if (weather !== undefined) state.world.weather = weather;
        if (season !== undefined) state.world.season = season;
        if (ambience !== undefined) state.ambience = ambience;
        const worker = state.world.agents.worker;
        if (options.activity !== undefined) worker.activity = options.activity;
        if (options.sleeping !== undefined) worker.sleeping = options.sleeping;
        if (task !== undefined)
          worker.task = task === null ? null : { type: task };
        if (path !== undefined) worker.path = path;
        if (position) Object.assign(worker, position);
        scene.sync();
        scene.update(time, 16);
        return snapshot();
      },
    };
  },
  () => {},
);
new Phaser.Game({
  type: Phaser.CANVAS,
  width: 1100,
  height: 760,
  parent: "game",
  scene: Scene,
  audio: { noAudio: true },
  banner: false,
});
