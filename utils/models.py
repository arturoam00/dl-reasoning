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
    CONJUCTION = "ConceptConjuction"


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
    def get_conjuncts(self) -> set["Concept"]:
        return set(Concept(concept) for concept in self._expr.getConjuncts())


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

    def get_top(self):
        return Concept(self._el_factory.getTop())
