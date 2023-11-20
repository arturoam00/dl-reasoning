"""
This are just convenient translations to Python classes
of the Java classes coming from dl4python.
"""

from enum import Enum

from utils.java_gateway import gateway

formatter = gateway.getSimpleDLFormatter()


class ConceptType(Enum):
    NAME = "ConceptName"
    TOP = "TopConcept$"
    EXISTENTIAL = "ExistentialRoleRestriction"
    CONJUNCTION = "ConceptConjunction"


class AxiomType(Enum):
    GCI = "GeneralConceptInclusion"
    EQUIVALENCE = "EquivalenceAxiom"


class BaseExpression:
    _expr: any

    def __init__(self, expr: any) -> None:
        self._expr = expr

    @property
    def type(self) -> str:
        return self._expr.getClass().getSimpleName()

    def __str__(self) -> str:
        return formatter.format(self._expr)


class ConceptName(BaseExpression):
    pass


class Concept(BaseExpression):
    @property
    def conjuncts(self) -> set["Concept"]:
        assert self.type == ConceptType.CONJUNCTION.value
        return set(Concept(concept) for concept in self._expr.getConjuncts())

    @property
    def role(self) -> "Concept":
        assert self.type == ConceptType.EXISTENTIAL.value
        return Concept(self._expr.role())

    @property
    def filler(self) -> "Concept":
        assert self.type == ConceptType.EXISTENTIAL.value
        return Concept(self._expr.filler())


class Axiom(BaseExpression):
    @property
    def rhs(self) -> Concept:
        return Concept(self._expr.rhs())

    @property
    def lhs(self) -> Concept:
        return Concept(self._expr.lhs())

    def get_concepts(self) -> set[Concept]:
        return set(Concept(concept) for concept in self._expr.getConcepts())


class ELFactory:
    _el_factory: any

    def __init__(self, el_factory: any) -> None:
        self._el_factory = el_factory

    def get_gci(self, A: Concept, B: Concept) -> Axiom:
        return Axiom(self._el_factory.getGCI(A._concept, B._concept))

    def get_top(self) -> Concept:
        return Concept(self._el_factory.getTop())

    def get_concept_name(self, name: str) -> Concept:
        return Concept(self._el_factory.getConceptName(name))

    def get_role(self, role_name: str) -> Concept:
        return Concept(self._el_factory.getRole(role_name))

    def get_conjunction(self, A: Concept, B: Concept) -> Concept:
        return Concept(self._el_factory.getConjunction(A._expr, B._expr))

    def get_existential_role_restriction(
        self, role: Concept, concept: Concept
    ) -> Concept:
        return Concept(
            self._el_factory.getExistentialRoleRestriction(role._expr, concept._expr)
        )
