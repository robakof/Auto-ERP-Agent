def get_backlog_by_id(self, backlog_id: int) -> dict | None:
          """Get a single backlog item by ID.

          NOTE: Delegates to BacklogRepository (M3 adapter pattern).
          """
          from core.repositories.backlog_repo import BacklogRepository
          from core.mappers.legacy_api import LegacyAPIMapper

          repo = self._get_repository(BacklogRepository)
          item = repo.get(backlog_id)
          if item is None:
              return None
          return LegacyAPIMapper.backlog_to_dict(item)
    def cmd_backlog(args: argparse.Namespace, bus: AgentBus) -> dict:
      if args.id:
          item = bus.get_backlog_by_id(args.id)
          if item is None:
              return {"ok": False, "error": f"Backlog item #{args.id} not found"}
          return {"ok": True, "data": item}
      entries = bus.get_backlog(status=args.status, area=args.area)
      return {"ok": True, "data": entries, "count": len(entries)}