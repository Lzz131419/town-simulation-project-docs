export interface Point {
  x: number;
  y: number;
}
export function pathDistance(start: Point, path: readonly Point[]): number {
  let distance = 0;
  for (const point of path) {
    distance += Math.hypot(point.x - start.x, point.y - start.y);
    start = point;
  }
  return distance;
}

/** Recover only the part of the old route the server actually traversed.
 * A shorter replacement route is not evidence that old waypoints were visited.
 * null means an authoritative relocation: snap instead of walking through walls.
 */
export function traversedPath(
  previous: Point,
  path: readonly Point[],
  current: Point,
): Point[] | null {
  if (Math.hypot(current.x - previous.x, current.y - previous.y) < 0.01)
    return [];
  const result: Point[] = [];
  let start = previous;
  for (const end of path) {
    const dx = end.x - start.x,
      dy = end.y - start.y;
    const length2 = dx * dx + dy * dy;
    if (length2 > 0) {
      const t =
        ((current.x - start.x) * dx + (current.y - start.y) * dy) / length2;
      if (
        t >= -0.00001 &&
        t <= 1.00001 &&
        Math.hypot(
          current.x - (start.x + t * dx),
          current.y - (start.y + t * dy),
        ) < 0.01
      )
        return [...result, { ...current }];
    }
    result.push({ ...end });
    start = end;
  }
  return null;
}
