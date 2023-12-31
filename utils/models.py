"""
This are just convenient translations to Python classes
of the Java classes coming from dl4python.
"""

from enum import Enum
from typing import Any, Optional

from utils import gateway

formatter = gateway.getSimpleDLFormatter()


class ConceptType(Enum):
    NAME = "ConceptName"
    TOP = "TopConcept$"
    EXISTENTIAL = "ExistentialRoleRestriction"
    CONJUNCTION = "ConceptConjunction"


class AxiomType(Enum):
    GCI = "GeneralConceptInclusion"
    EQUIVALENCE = "EquivalenceAxiom"


JavaObject = Any


class BaseExpression:
    """
    Base encapsulating class for the Java objects
    coming from dl4python. The Java object is kept
    in `_expr`

    Mainly useful for concepts and axioms so far
    """

    _expr: JavaObject

    def __init__(self, expr: JavaObject) -> None:
        self._expr = expr

    @property
    def type(self) -> str:
        return self._expr.getClass().getSimpleName()

    def __eq__(self, __value: object) -> bool:
        return self._expr == __value._expr

    def __hash__(self) -> int:
        return hash(self._expr)

    def __str__(self) -> str:
        return formatter.format(self._expr)


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
        assert self.type == AxiomType.GCI.value
        return Concept(self._expr.rhs())

    @property
    def lhs(self) -> Concept:
        assert self.type == AxiomType.GCI.value
        return Concept(self._expr.lhs())

    def get_concepts(self) -> set[Concept]:
        return set(Concept(concept) for concept in self._expr.getConcepts())


class ELFactory:
    """
    Encapsulating the class returned by getELFactory()

    Java object is kept in _el_factory

    It's important to remember to pass the actual Java
    objects to the Java methods and not the Python objects

    One does it accessing the `_expr` attribute
    """

    _instance: Optional["ELFactory"] = None
    _el_factory: Optional[JavaObject] = None

    def __new__(cls, *args, **kwargs) -> "ELFactory":
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._el_factory = gateway.getELFactory()
        return cls._instance

    def get_gci(self, A: Concept, B: Concept) -> Axiom:
        return Axiom(self._el_factory.getGCI(A._expr, B._expr))

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
