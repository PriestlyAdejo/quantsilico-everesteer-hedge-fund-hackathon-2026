class RoundController:
    """Restartable open-round pull -> infer -> guard -> submit -> observe loop."""

    def tick(self):
        raise NotImplementedError
