from qs_everesteer.contracts import EventCapabilities


class EveresteerEventAdapter:
    """Thin capability-detecting wrapper around the installed everestapi."""

    def inspect(self) -> EventCapabilities:
        raise NotImplementedError

    def pull(self, split: str, output_path: str) -> None:
        raise NotImplementedError
