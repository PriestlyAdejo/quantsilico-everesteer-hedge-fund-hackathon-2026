def score_with_official_engine(*args, **kwargs):
    """Wrap everestapi.scoring; never silently replace it with an approximation."""
    raise NotImplementedError
