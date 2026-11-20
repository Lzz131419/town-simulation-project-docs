import definition from "../../../shared/world-map.json";
export const layout = definition;
export interface CameraArea {
  x: number;
  y: number;
  width: number;
  height: number;
}
export const inRiver = (x: number) =>
  x >= layout.river.x && x < layout.river.x + layout.river.width;
export const onBridge = (x: number, y: number) =>
  layout.bridges.some(
    (b) => x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h,
  );
