import * as vscode from "vscode";

/**
 * RoleLayout — maps each agent role to a VS Code editor group (ViewColumn).
 * Multiple terminals of the same role become tabs within one group.
 */
export class RoleLayout {
  private roleColumns: Map<string, vscode.ViewColumn> = new Map();
  private roleTerminals: Map<string, vscode.Terminal[]> = new Map();
  private nextColumn: number = 1;
  private carouselIndex: number = 0;

  /** Get or assign a ViewColumn for the given role. */
  getViewColumn(role: string): vscode.ViewColumn {
    let col = this.roleColumns.get(role);
    if (!col) {
      col = this.nextColumn as vscode.ViewColumn;
      this.nextColumn++;
      this.roleColumns.set(role, col);
    }
    return col;
  }

  /** Register a terminal under a role. */
  addTerminal(role: string, terminal: vscode.Terminal): void {
    const list = this.roleTerminals.get(role) || [];
    list.push(terminal);
    this.roleTerminals.set(role, list);
  }

  /** Unregister a terminal (called by Watcher on close). */
  removeTerminal(terminal: vscode.Terminal): void {
    for (const [role, list] of this.roleTerminals) {
      const idx = list.indexOf(terminal);
      if (idx !== -1) {
        list.splice(idx, 1);
        if (list.length === 0) {
          this.roleTerminals.delete(role);
          // Keep roleColumns mapping — column stays reserved
        }
        return;
      }
    }
  }

  /** Focus the first terminal of a given role. */
  focusRole(role: string): boolean {
    const list = this.roleTerminals.get(role);
    if (list && list.length > 0) {
      list[0].show();
      return true;
    }
    return false;
  }

  /** Carousel: cycle to next terminal across all roles. */
  rotateNext(): string | null {
    const all = this.getAllTerminals();
    if (all.length === 0) {
      return null;
    }
    this.carouselIndex = this.carouselIndex % all.length;
    const { role, terminal } = all[this.carouselIndex];
    terminal.show();
    this.carouselIndex = (this.carouselIndex + 1) % all.length;
    return role;
  }

  /** Get flat list of all tracked terminals with their roles. */
  private getAllTerminals(): Array<{ role: string; terminal: vscode.Terminal }> {
    const result: Array<{ role: string; terminal: vscode.Terminal }> = [];
    for (const [role, list] of this.roleTerminals) {
      for (const terminal of list) {
        result.push({ role, terminal });
      }
    }
    return result;
  }

  /** Get active role count (for diagnostics). */
  get activeRoles(): number {
    return this.roleTerminals.size;
  }
}
