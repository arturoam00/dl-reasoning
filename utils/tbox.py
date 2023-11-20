from copy import copy

from utils.models import Axiom, AxiomType, ConceptType, ELFactory


class TBox:
    axioms: set[Axiom]
    el_factory: ELFactory

    def __init__(self, axioms: set[Axiom], el_factory: ELFactory) -> None:
        self.axioms = axioms
        self.el_factory = el_factory

    def resolve_equivalence(self, equivalence: Axiom) -> set:
        A, B = equivalence.get_concepts()
        return {self.el_factory.get_gci(A, B), self.el_factory.get_gci(B, A)}

    def resolve_gci(self, gci: Axiom) -> set[Axiom]:
        if gci.rhs.type == ConceptType.CONJUCTION.value:
            return {
                self.el_factory.get_gci(gci.lhs, concept)
                for concept in gci.rhs.conjuncts
            }
        else:
            return {gci}

        # one should include a lot more, but i think dl4python
        # already does it (?)

    def _normalize_axioms(self, axioms: set[Axiom]) -> tuple[set[Axiom], bool]:
        axioms = copy(axioms)
        normalized = set()
        terminate = True

        for axiom in axioms:
            if axiom.type == AxiomType.EQUIVALENCE.value:
                normalized |= self.resolve_equivalence(axiom)
                terminate = False

            elif axiom.type == AxiomType.GCI.value:
                normalized |= self.resolve_gci(axiom)
                terminate = False

            else:
                normalized |= axiom

        return normalized, terminate

    def get_normalized_axioms(self) -> set[Axiom]:
        terminate = False
        axioms = self.axioms
        while not terminate:
            axioms, terminate = self._normalize_axioms(axioms)

        return axioms
