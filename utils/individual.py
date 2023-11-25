from collections import defaultdict
from typing import DefaultDict, Optional, Set

from utils.models import Concept, ELFactory

el_factory = ELFactory()
top = el_factory.get_top()


class Individual:
    """
    Individual must be initialized with initial concept

    The initial concept and further added concepts are
    stored in the `concepts` set

    Successors relations are stored in `successors` in the form:

    `{role: set(role-successors)}`

    where the `role` is the key and the value is a set containing
    all the individuals connected by `role` found
    """

    initial_concept: Concept
    concepts: Set[Concept]
    successors: DefaultDict[Concept, Set[Optional["Individual"]]]

    def __init__(self, initial_concept: Concept) -> None:
        self.initial_concept = initial_concept
        self.concepts = {top, self.initial_concept}
        self.successors = defaultdict(set)

    def add_concept(self, concept: Concept) -> None:
        self.concepts.add(concept)

    def add_successor(self, role: Concept, successor: "Individual") -> None:
        self.successors[role].add(successor)

    def __eq__(self, __value: object) -> bool:
        return self.initial_concept == __value.initial_concept

    def __hash__(self) -> int:
        return hash(self.initial_concept)

    def __str__(self) -> str:
        return str(self.initial_concept)


RelationsDict = DefaultDict[Concept, Set[Individual]]
