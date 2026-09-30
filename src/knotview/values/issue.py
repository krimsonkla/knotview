"""One thing the project's own integrity check reports, as the overview's card draws it."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class Issue:
    """An issue's line, the file it names, and the documents it can link to.

    The path is kept as knot states it, absolute, and shown relative to the project when it lies
    inside it, since a reader knows their own project and not the machine's directory layout.
    Only codes whose ids were checked against knot to be documents it will show carry
    `document_ids`: a code's name is written for people, and one that sounds like a document can
    name a ticket, or an id knot refuses as ambiguous. Everything else is text, so a code knot adds
    later is shown plainly rather than linked somewhere that answers "nothing here".
    """

    text: str
    path: str = ""
    shown: str = ""
    document_ids: tuple[str, ...] = ()

    @classmethod
    def found(cls, text: str, path: str, root: Path, document_ids: tuple[str, ...] = ()) -> "Issue":
        """An issue with its path shown the one way every reader of issues shows it.

        knot writes some paths into its own message too, absolute, so the project's root is taken
        off those as well; a path outside the project is left as knot wrote it.
        """
        text = text.replace(f"{root}/", "") if str(root) not in ("", ".", "/") else text
        if not path:
            return cls(text=text, document_ids=document_ids)
        full = Path(path)
        shown = str(full.relative_to(root)) if full.is_relative_to(root) else path
        return cls(text=text, path=path, shown=shown, document_ids=document_ids)
