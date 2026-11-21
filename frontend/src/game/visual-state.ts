import type { SceneState } from "./scene-types";

export type Season = NonNullable<SceneState["world"]["season"]>;

export function weatherVisuals(
  world: Pick<SceneState["world"], "weather" | "season">,
  ambience: boolean,
  reducedMotion: boolean,
) {
  const snow =
    world.season === "winter" &&
    (world.weather === "rain" || world.weather === "cloudy");
  const storm = world.weather === "storm";
  const cloudy = world.weather === "cloudy";
  const precipitation = !ambience
    ? "none"
    : snow
      ? "snow"
      : storm || world.weather === "rain"
        ? "rain"
        : "none";
  return {
    precipitation,
    count:
      precipitation === "none"
        ? 0
        : Math.floor(
            (snow ? 100 : storm ? 260 : 140) / (reducedMotion ? 2 : 1),
          ),
    slant: storm ? 14 : 5,
    length: storm ? 22 : 14,
    shade: ambience ? (storm ? 0.22 : cloudy ? 0.05 : snow ? 0.04 : 0) : 0,
    fog: ambience && cloudy,
    motes: ambience ? (cloudy ? 48 : 24) : 0,
    ripples: precipitation === "rain" ? (storm ? 32 : 18) : 0,
  } as const;
}

// Two poses of the existing image; all transforms reset as soon as work stops.
export function workPose(
  task: string | undefined,
  time: number,
  reducedMotion = false,
) {
  const pose = { x: 0, y: 0, angle: 0, height: 48 };
  if (reducedMotion) return pose;
  if (
    [
      "farm",
      "harvest_veg",
      "harvest_flax",
      "gather",
      "gather_honey",
      "forage",
    ].includes(task ?? "")
  ) {
    if (Math.floor(time / 550) % 2) return { ...pose, y: 2, height: 41 };
  } else if (task === "chop" || task === "craft") {
    const strike = Math.floor(time / 380) % 2;
    return { ...pose, x: strike ? 1.5 : -1, angle: strike ? 9 : -7 };
  } else if (task === "fish") {
    const phase = time % 2600;
    if (phase < 180) return { ...pose, x: 1, angle: -4 };
    if (phase < 360) return { ...pose, x: -1, angle: 3 };
  } else if (task === "play") {
    // Two small hops reuse the existing sprite pose pipeline.
    const hop = Math.floor(time / 260) % 2;
    return { ...pose, y: hop ? -4 : 1, height: hop ? 45 : 48 };
  }
  return pose;
}
