class SubmissionGuard:
    """Hard integrity checks: lane, IDs, artefact, event identity, quota."""

    def validate(self, **kwargs):
        raise NotImplementedError
