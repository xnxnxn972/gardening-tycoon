import type { Wave } from '../data/waves';

interface QueuedSpawn {
  time: number;
  enemyId: string;
}

export class WaveSystem {
  /** 1-based once the first wave starts; 0 before that. */
  currentWave = 0;
  readonly totalWaves: number;

  private readonly waves: Wave[];
  private queue: QueuedSpawn[] = [];
  private elapsed = 0;

  constructor(waves: Wave[]) {
    this.waves = waves;
    this.totalWaves = waves.length;
  }

  get remainingToSpawn(): number {
    return this.queue.length;
  }

  get isLastWave(): boolean {
    return this.currentWave >= this.totalWaves;
  }

  /** Builds the spawn queue for the next wave. Returns false if all waves are done. */
  startNextWave(): boolean {
    if (this.isLastWave) return false;
    this.currentWave++;
    const wave = this.waves[this.currentWave - 1];
    this.queue = [];
    for (const entry of wave) {
      for (let i = 0; i < entry.count; i++) {
        this.queue.push({ time: entry.startDelay + i * entry.interval, enemyId: entry.enemy });
      }
    }
    this.queue.sort((a, b) => a.time - b.time);
    this.elapsed = 0;
    return true;
  }

  update(dt: number, spawn: (enemyId: string) => void): void {
    if (this.queue.length === 0) return;
    this.elapsed += dt;
    while (this.queue.length > 0 && this.queue[0].time <= this.elapsed) {
      spawn(this.queue.shift()!.enemyId);
    }
  }
}
