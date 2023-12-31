"""One problem with the tbox coming from dl4python
are equivalence axioms, which should be converted to
conjunctions to deal with them.

This is done normalizing the tbox.

Question is, should we take into account other things 
when normalizing the tbox coming from dl4python? 
"""
from copy import copy
from typing import Set, Tuple

from utils.models import Axiom, AxiomType, ELFactory

el_factory = ELFactory()


class TBox:
    axioms: Set[Axiom]
    normalized: Set[Axiom]

    def __init__(self, axioms: Set[Axiom]) -> None:
        self.axioms = axioms
        self.normalized = self.get_normalized_axioms()

    def resolve_equivalence(self, equivalence: Axiom) -> Set[Axiom]:
        A, B = equivalence.get_concepts()
        return {el_factory.get_gci(A, B), el_factory.get_gci(B, A)}

    def resolve_gci(self, gci: Axiom) -> Set[Axiom]:
        """Should one deal with more stuff in the TBox ?"""
        raise NotImplementedError

    def _normalize_axioms(
        self,
        axioms: Set[Axiom],
    ) -> Tuple[Set[Axiom], bool]:
        normalized = set()
        terminate = True

        for axiom in axioms:
            if axiom.type == AxiomType.EQUIVALENCE.value:
                normalized |= self.resolve_equivalence(axiom)
                terminate = False
            else:
                normalized.add(axiom)

        return normalized, terminate

    def get_normalized_axioms(self) -> Set[Axiom]:
        terminate = False
        axioms = copy(self.axioms)
        while not terminate:
            axioms, terminate = self._normalize_axioms(axioms)

        return axioms
