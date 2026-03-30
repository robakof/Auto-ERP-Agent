import { MrowiskoDB } from "./db";
import { LiveAgent } from "./types";

/**
 * Backward-compatibility wrapper over MrowiskoDB.
 * Keeps Spawner/Watcher/Commands working without changes (Faza 1).
 * Will be removed in Faza 2 when consumers switch to MrowiskoDB directly.
 */
export class Registry {
  constructor(private db: MrowiskoDB) {}

  insert(
    spawnToken: string,
    role: string,
    task: string,
    terminalName: string,
    spawnedBy: string
  ): void {
    this.db.insertAgent(spawnToken, role, task, terminalName, spawnedBy);
  }

  getActiveAgents(): LiveAgent[] {
    return this.db.getActiveAgents();
  }

  markStopped(sessionId: string): void {
    this.db.markStopped(sessionId);
  }

  cleanup(): void {
    this.db.cleanup();
  }

  dispose(): void {
    // DB lifecycle managed by activate() — not here
  }
}
