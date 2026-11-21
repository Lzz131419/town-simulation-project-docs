import type { Town } from "../types";

export function isMarketDay(world: Pick<Town, "tick" | "market_day">) {
  return world.tick < (world.market_day?.until_tick ?? 0);
}
