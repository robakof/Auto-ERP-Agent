import * as vscode from "vscode";
import { MrowiskoDB } from "./db";

/**
 * GarbageCollector — autopoke stale agents before killing.
 *
 * Flow:
 * 1. Agent active, last_activity > staleThreshold → status=warned + poke
 * 2. Agent warned, last_activity > graceThreshold → status=stopped (GC kill)
 *
 * Config: config/gc_policy.json (thresholds in minutes)
 */

interface GcPolicy {
  staleThresholdMinutes: number;
  graceMinutes: number;
  intervalMinutes: number;
}

const DEFAULT_POLICY: GcPolicy = {
  staleThresholdMinutes: 60,
  graceMinutes: 15,
  intervalMinutes: 5,
};

export class GarbageCollector {
  private timer: ReturnType<typeof setInterval> | undefined;

  constructor(
    private db: MrowiskoDB,
    private log: vscode.LogOutputChannel,
    private policyFile: string
  ) {}

  start(): void {
    const policy = this.readPolicy();
    this.timer = setInterval(() => this.cycle(), policy.intervalMinutes * 60_000);
    this.log.info("GC started", { ...policy });
  }

  private readPolicy(): GcPolicy {
    try {
      const fs = require("fs");
      const raw = JSON.parse(fs.readFileSync(this.policyFile, "utf-8"));
      return {
        staleThresholdMinutes: raw.staleThresholdMinutes ?? DEFAULT_POLICY.staleThresholdMinutes,
        graceMinutes: raw.graceMinutes ?? DEFAULT_POLICY.graceMinutes,
        intervalMinutes: raw.intervalMinutes ?? DEFAULT_POLICY.intervalMinutes,
      };
    } catch {
      return DEFAULT_POLICY;
    }
  }

  private cycle(): void {
    const policy = this.readPolicy();

    try {
      // Phase 1: warned agents past grace period → stopped
      const expired = this.db.getWarnedAgents(policy.graceMinutes);
      for (const agent of expired) {
        if (agent.sessionId) {
          this.db.markStopped(agent.sessionId);
          this.log.warn("GC killed agent (no response after warning)", {
            role: agent.role,
            sessionId: agent.sessionId,
          });
        }
      }

      // Phase 2: stale active agents → warned + poke
      const stale = this.db.getStaleAgents(policy.staleThresholdMinutes);
      for (const agent of stale) {
        if (agent.sessionId && agent.terminalName) {
          this.db.markWarned(agent.sessionId);
          this.pokeAgent(agent.terminalName);
          this.log.info("GC warned agent (stale)", {
            role: agent.role,
            sessionId: agent.sessionId,
          });
        }
      }
    } catch (e) {
      this.log.error("GC cycle error", { error: String(e) });
    }
  }

  private pokeAgent(terminalName: string): void {
    const terminal = vscode.window.terminals.find((t) => t.name === terminalName);
    if (terminal) {
      terminal.sendText("", true);
      setTimeout(() => {
        terminal.sendText("[GC] Brak aktywności. Odpowiedz lub sesja zostanie zamknięta.");
      }, 300);
    }
  }

  dispose(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
  }
}
