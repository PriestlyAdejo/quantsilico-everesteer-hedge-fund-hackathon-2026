class RacingScheduler:
    """Successive-halving-inspired budget allocator using soft quality evidence."""

    def next_actions(self, research_state: dict) -> list[dict]:
        raise NotImplementedError
