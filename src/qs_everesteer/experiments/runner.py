class ExperimentRunner:
    """Config -> model -> OOF -> metrics -> artefacts -> immutable run manifest."""

    def run(self, config_path: str):
        raise NotImplementedError
