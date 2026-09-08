from dataclasses import dataclass
from djangospice_widget.interaction import Interaction


@dataclass(frozen=True, slots=True)
class PageContext:
    number: int
    total: int

    has_previous: bool
    has_next: bool

    previous: Interaction | None
    next: Interaction | None

    first: Interaction | None
    last: Interaction | None

    pages: tuple[
        tuple[int, Interaction, bool],
        ...
    ]