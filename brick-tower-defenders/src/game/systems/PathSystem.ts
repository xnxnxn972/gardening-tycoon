import type { Vec2 } from '../data/levelCastle';
import { clamp, dist } from '../utils/math';

export interface PathPoint extends Vec2 {
  segIndex: number;
  /** Distance from the path start to this point, used as "progress toward the core". */
  progress: number;
}

export class PathSystem {
  readonly points: Vec2[];
  /** Cumulative distance from the start up to each waypoint. */
  readonly cumulative: number[];
  readonly totalLength: number;

  constructor(points: Vec2[]) {
    this.points = points;
    this.cumulative = [0];
    let total = 0;
    for (let i = 1; i < points.length; i++) {
      total += dist(points[i - 1].x, points[i - 1].y, points[i].x, points[i].y);
      this.cumulative.push(total);
    }
    this.totalLength = total;
  }

  /** Closest point on the polyline to (x, y) — used to place squad rally points. */
  closestPoint(x: number, y: number): PathPoint {
    let best: PathPoint = { x: this.points[0].x, y: this.points[0].y, segIndex: 0, progress: 0 };
    let bestDist = Infinity;
    for (let i = 0; i < this.points.length - 1; i++) {
      const a = this.points[i];
      const b = this.points[i + 1];
      const abx = b.x - a.x;
      const aby = b.y - a.y;
      const lenSq = abx * abx + aby * aby;
      const t = lenSq === 0 ? 0 : clamp(((x - a.x) * abx + (y - a.y) * aby) / lenSq, 0, 1);
      const px = a.x + abx * t;
      const py = a.y + aby * t;
      const d = dist(x, y, px, py);
      if (d < bestDist) {
        bestDist = d;
        best = {
          x: px,
          y: py,
          segIndex: i,
          progress: this.cumulative[i] + Math.sqrt(lenSq) * t
        };
      }
    }
    return best;
  }
}
