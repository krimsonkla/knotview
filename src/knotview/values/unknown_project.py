"""The refusal raised when a saved project cannot be found or cannot be saved."""


class UnknownProject(Exception):
    """A name nobody saved, a name that is no name, or a setting that cannot be what it says.

    It carries advice like the backlog's refusal does, because the likeliest cause is a name typed
    from memory, and the remedy is the list of names that exist, or the command that saves one.
    """

    def __init__(self, message: str, *, advice: str) -> None:
        super().__init__(f"{message}. {advice}")
        self.message = message
        self.advice = advice
