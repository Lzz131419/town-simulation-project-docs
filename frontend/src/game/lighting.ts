// World time, not wall-clock time, owns the day/night cycle.
const keys = [
  [0, 0.34, 0, 1],
  [5, 0.34, 0, 1],
  [6, 0.16, 0.08, 0.5],
  [8, 0, 0, 0],
  [16, 0, 0, 0],
  [18, 0.09, 0.14, 0.4],
  [20, 0.34, 0, 1],
  [24, 0.34, 0, 1],
];
export function daylight(tick: number) {
  const hour = ((((480 + tick * 10) % 1440) + 1440) % 1440) / 60;
  const index = keys.findIndex(
    (k, i) => i < keys.length - 1 && hour >= k[0] && hour < keys[i + 1][0],
  );
  const a = keys[Math.max(0, index)],
    b = keys[Math.max(0, index) + 1];
  const t = (hour - a[0]) / (b[0] - a[0]),
    eased = t * t * (3 - 2 * t);
  const mix = (i: number) => a[i] + (b[i] - a[i]) * eased;
  return { night: mix(1), warmth: mix(2), lamps: mix(3) };
}
