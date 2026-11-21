import type { Town, Catalog, TownEvent } from "../types";
export interface SceneState {
  world: Town & {
    weather?: "sunny" | "cloudy" | "rain" | "storm";
    season?: "spring" | "summer" | "autumn" | "winter";
  };
  self: string;
  selected: string;
  names: boolean;
  routes: boolean;
  ambience: boolean;
  follow: boolean;
  catalog: Catalog;
  events: TownEvent[];
}
export type SceneReader = () => SceneState;
export type SceneEmit = (
  event: "place" | "select" | "freeCamera",
  value: string,
) => void;
