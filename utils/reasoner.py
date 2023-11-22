import logging
from collections import defaultdict
from dataclasses import dataclass, field

from utils import gateway
from utils.models import Axiom, AxiomType, Concept, ConceptType, ELFactory
from utils.tbox import TBox

el_factory = ELFactory(gateway.getELFactory())

logger = logging.getLogger(__name__)


@dataclass
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

    concepts: set[Concept] = field(default_factory=set)

    successors: dict[Concept, set["Individual"]] = field(
        default_factory=lambda: defaultdict(set)
    )

    def add_concept(self, concept: Concept) -> None:
        self.concepts.add(concept)

    def add_successor(self, role: Concept, successor: "Individual") -> None:
        self.successors[role].add(successor)

    def __eq__(self, __value: object) -> bool:
        return self.initial_concept == __value.initial_concept

    def __hash__(self) -> int:
        return hash(self.initial_concept)

    def __str__(self) -> str:
        concepts = ""
        for concept in self.concepts:
            concepts += f"{'':<4}{concept}\n"

        return f"{self.initial_concept}\n{concepts}"


RelationsDict = dict[Concept, set[Individual]]


class Model:
    """
    This class can build a model for an ontology so
    one can check whether

    O |= A ⊑ B

    given the concepts A and B

    This is done by applying the EL-Completion Rules:
        - ⊤-rule: Add ⊤ to any individual.

        - ⊓-rule 1: If d has C ⊓ D assigned, assign also C and D to d.

        - ⊓-rule 2: If d has C and D assigned, assign also C ⊓ D to d.

        - ∃-rule 1: If d has ∃r .C assigned:

            1. If there is an element e with initial concept C assigned, make
            e the r -successor of d.

            2. Otherwise, add a new r -successor to d, and assign to it as
            initial concept C .

        - ∃-rule 2: If d has an r -successor with C assigned, add ∃r .C to d.

        - ⊑-rule: If d has C assigned and C ⊑ D ∈ T , then also assign D to d


    Using the EL-Completion Algorithm:
        Decide whether O |= C0 ⊑ D0

        1. Start with initial element d0 , assigned as initial concept C0 .

        2. Apply the EL-completion rules exhaustively, with the restriction that only
        concepts from the input are assigned.
    """

    input_concepts: set[Concept]
    axioms: set[Axiom]
    individuals: set[Individual]

    _temp_individuals: set[Individual]

    log: logging.Logger

    def __init__(self, input_concepts: set[Concept], axioms: set[Axiom]) -> None:
        self.input_concepts = input_concepts
        self.gci_axioms = set(
            axiom for axiom in axioms if axiom.type == AxiomType.GCI.value
        )
        self.individuals = set()

        self._temp_individuals = set()

        self.log = logger.getChild("Model")

    def get_new_concepts(self, *args: Concept | set[Concept]) -> set[Concept]:
        """We have found some potentially new concepts to add to the individual,
        but first one have to check whether the concepts are present in the
        input concepts
        """
        concepts = set()

        for concept in args:
            if isinstance(concept, Concept) and concept in self.input_concepts:
                concepts.add(concept)
            elif isinstance(concept, set):
                concepts |= set(c for c in concept if c in self.input_concepts)

        return concepts

    def get_new_concepts_from_successor(
        self, role: Concept, successor: Individual
    ) -> set[Concept]:
        concepts = set()

        for concept in successor.concepts:
            concepts |= self.get_new_concepts(
                el_factory.get_existential_role_restriction(role, concept)
            )
        return concepts

    def get_new_concepts_from_tbox(self, concept: Concept) -> set[Concept]:
        concepts = set()

        for axiom in self.gci_axioms:
            if concept == axiom.lhs:
                concepts |= self.get_new_concepts(axiom.rhs)

        return concepts

    def get_new_individual(self, concept: Concept) -> Individual:
        # If there is an element `individual` with initial concept `concept` assigned,
        # return that element
        for inidividual in self.individuals:
            if inidividual.initial_concept == concept:
                return inidividual

        # Otherwise, create a new individual with initial concept `concept`
        new_individual = Individual(concept)
        self.zero_rule(new_individual)
        self._temp_individuals.add(new_individual)

        return new_individual

    def zero_rule(self, individual: Individual) -> None:
        """⊤-rule: Add ⊤ to any individual."""
        individual.add_concept(el_factory.get_top())

        # i also add the initial concept to the individual's concepts
        individual.add_concept(individual.initial_concept)

    def first_conj_rule(self, individual: Individual) -> set[Concept]:
        """⊓-rule 1: If d has C ⊓ D assigned, assign also C and D to d."""
        new_concepts = set()

        for concept in individual.concepts:
            if concept.type == ConceptType.CONJUNCTION.value:
                new_concepts |= self.get_new_concepts(concept.conjuncts)

        return new_concepts

    def second_conj_rule(self, individual: Individual) -> set[Concept]:
        """⊓-rule 2: If d has C and D assigned, assign also C ⊓ D to d."""
        new_concepts = set()

        for first_concept in individual.concepts:
            for second_concept in individual.concepts:
                conjunction = el_factory.get_conjunction(first_concept, second_concept)
                new_concepts |= self.get_new_concepts(conjunction)

        return new_concepts

    def first_exist_rule(self, individual: Individual) -> RelationsDict:
        """∃-rule 1: If d has ∃r .C assigned:

        1. If there is an element e with initial concept C assigned, make
        e the r -successor of d.

        2. Otherwise, add a new r -successor to d, and assign to it as
        initial concept C .
        """
        new_relations = defaultdict(set)

        for concept in individual.concepts:
            if concept.type == ConceptType.EXISTENTIAL.value:
                new_relations[concept.role].add(self.get_new_individual(concept.filler))

        return new_relations

    def second_exist_rule(self, individual: Individual) -> set[Concept]:
        """∃-rule 2: If d has an r -successor with C assigned, add ∃r .C to d."""
        new_concepts = set()

        for role, successors in individual.successors.items():
            for successor in successors:
                new_concepts |= self.get_new_concepts_from_successor(role, successor)

        return new_concepts

    def contained_rule(self, individual: Individual) -> set[Concept]:
        """⊑-rule: If d has C assigned and C ⊑ D ∈ T , then also assign D to d"""
        new_concepts = set()

        for concept in individual.concepts:
            new_concepts |= self.get_new_concepts_from_tbox(concept)

        return new_concepts

    def apply_rules(self, subsumee: Concept, subsumer: Concept) -> bool:
        """Decide whether O |= `subsumee` ⊑ `subsumer`

        1. Start with initial element `child`, assigned as initial concept `subsumee`.

        2. Apply the EL-completion rules exhaustively, with the restriction that only
        concepts from the input are assigned.
        """
        # create and add first individual to model
        child = Individual(subsumee)
        self.individuals.add(child)

        # ⊤-rule
        self.zero_rule(child)

        # rules that can add concepts to individuals
        concept_rules = [
            self.first_conj_rule,  # ⊓-rule 1
            self.second_conj_rule,  # ⊓-rule 2
            self.second_exist_rule,  # ∃-rule 2
            self.contained_rule,  # ⊑-rule
        ]

        CHANGED = True
        while CHANGED:
            CHANGED = False
            # loop over all individuals in model
            for individual in self.individuals:
                # apply rules ⊓-rule 1, ⊓-rule 2, ∃-rule 2 and ⊑-rule
                for rule in concept_rules:
                    new_concepts = rule(individual)
                    CHANGED = True if not new_concepts <= individual.concepts else False
                    individual.concepts |= new_concepts

                # ∃-rule 1
                # this rule can't add concepts but successors
                new_relations = self.first_exist_rule(individual)
                CHANGED = (
                    True
                    if not new_relations.items() <= individual.successors.items()
                    else False
                )
                individual.successors.update(new_relations)

            # add potentially newly created individuals (in ∃-rule 1) to model
            self.individuals |= self._temp_individuals

        return subsumer in child.concepts


class ELReasoner:
    tbox: TBox
    concepts: set[Concept]
    concept_names: set[Concept]
    # hierarchy: dict[str, set[Concept]]

    log: logging.Logger

    def __init__(self, ontology: any) -> None:
        self.tbox = TBox(
            set(Axiom(axiom) for axiom in ontology.tbox().getAxioms()), el_factory
        )
        self.concepts = set(Concept(c) for c in ontology.getSubConcepts())
        self.concept_names = set(Concept(c) for c in ontology.getConceptNames())

        # self.hierarchy = defaultdict(set)

        self.log = logger.getChild("ELReasoner")

    def is_subsumed_by(self, subsumee: str | Concept, subsumer: str | Concept) -> str:
        concepts = {"subsumee": subsumee, "subsumer": subsumer}
        for id, concept in concepts.items():
            if isinstance(concept, str):
                concepts[id] = el_factory.get_concept_name(concept)

        assert set(concepts.values()) <= self.concepts

        model = Model(input_concepts=self.concepts, axioms=self.tbox.normalized)
        return model.apply_rules(**concepts)

    def classify(self) -> None:
        raise NotImplementedError

    def print_hierarchy(self) -> None:
        raise NotImplementedError

    def get_concept_hierarchy(self, concept_name: str, upwards: bool = True) -> None:
        concepts = set()
        for concept in self.concept_names:
            result = (
                self.is_subsumed_by(subsumee=concept_name, subsumer=concept)
                if upwards
                else self.is_subsumed_by(subsumee=concept, subsumer=concept_name)
            )

            if result:
                concepts.add(concept)

        for c in concepts:
            print(c)
