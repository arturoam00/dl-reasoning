import logging
from collections import defaultdict

from utils import gateway
from utils.model import Model
from utils.models import Axiom, Concept, ELFactory
from utils.tbox import TBox

logger = logging.getLogger(__name__)

el_factory = ELFactory()


class ELReasoner:
    tbox: TBox
    concepts: set[Concept]
    concept_names: set[Concept]
    hierarchy: dict[str, set[Concept]]
    is_classified: bool

    log: logging.Logger

    def __init__(self, ontology: any) -> None:
        self.tbox = TBox(
            set(Axiom(axiom) for axiom in ontology.tbox().getAxioms()), el_factory
        )
        self.concepts = set(Concept(c) for c in ontology.getSubConcepts())
        self.concept_names = set(Concept(c) for c in ontology.getConceptNames())

        self.hierarchy = defaultdict(set)
        self.is_classified = False

        self.log = logger.getChild("ELReasoner")

    def log_results(self, subsumee: Concept, subsumer: Concept, result: bool) -> None:
        msg = (
            f"{subsumee} IS subsumed by {subsumer}\n\n"
            if result
            else f"{subsumee} is NOT subsumed by {subsumer}"
        )
        self.log.info(msg)
        self.log.info(f"The subsumers of {subsumee} have been added to hierarchy\n\n")

    def is_subsumed_by(self, subsumee: str | Concept, subsumer: str | Concept) -> bool:
        concepts = {"subsumee": subsumee, "subsumer": subsumer}
        for id, concept in concepts.items():
            if isinstance(concept, str):
                concepts[id] = el_factory.get_concept_name(concept)

        assert set(concepts.values()) <= self.concepts

        self.log.info(f"Trying to find a model for O |= {subsumee} ⊑ {subsumer}\n\n")

        input_concepts = self.concepts | set(concepts.values())

        model = Model(input_concepts=input_concepts, axioms=self.tbox.normalized)

        result = model.apply_rules(**concepts)

        self.hierarchy[subsumee] |= set(
            c for c in model.initial_individual.concepts if c in self.concept_names
        )

        self.log_results(subsumee, subsumer, result)

        return result

    def classify(self) -> None:
        top = el_factory.get_top()
        for concept in self.concept_names:
            self.is_subsumed_by(subsumee=concept, subsumer=top)

        self._complete_hierarchy()
        self.is_classified = True

    def get_subsumers(self, subsumee: str | Concept) -> None:
        if isinstance(subsumee, str):
            subsumee = el_factory.get_concept_name(subsumee)

        if self.is_classified:
            for c in self.hierarchy[subsumee]:
                print(c)
                return

        self._fill_all_subsumers(subsumee)

        for c in self.hierarchy[subsumee]:
            print(c)

    def _fill_all_subsumers(self, subsumee: Concept) -> None:
        top = el_factory.get_top()
        added = set()

        if not self.hierarchy.get(subsumee):
            self.is_subsumed_by(subsumee, top)

        for subsumer in self.hierarchy[subsumee]:
            if not self.hierarchy.get(subsumer):
                self.is_subsumed_by(subsumer, top)

            added |= self.hierarchy[subsumer] - self.hierarchy[subsumee]

        self.hierarchy[subsumee] |= added
        if added:
            self._fill_all_subsumers(subsumee)
        else:
            return

    def _complete_hierarchy(self) -> None:
        for subsumee in self.hierarchy:
            self._fill_all_subsumers(subsumee)
