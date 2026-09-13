"""The refusal raised when a backlog cannot be read as one."""


class UnreadableBacklog(Exception):
    """knot answered with something this panel cannot read, or did not answer at all.

    One refusal for the whole reading path, because every case is the same thing from the panel's
    point of view: the backlog could not be established. What differs is the advice, which is why
    the advice is a field rather than a sentence buried in a message.

    It carries advice because a panel that says only "failed" sends its reader to the logs. The
    likeliest causes are a directory that is not a knot project and a knot whose answer shape moved,
    and those have different remedies.
    """

    def __init__(self, message: str, *, advice: str, code: str | None = None) -> None:
        super().__init__(f"{message}. {advice}")
        self.message = message
        self.advice = advice
        # knot's own error code where the refusal came from an envelope, so a caller can tell a
        # ticket that is not there from a backlog that cannot be read, without parsing the message.
        self.code = code
