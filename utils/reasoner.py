import logging
from collections import defaultdict
from typing import Any, DefaultDict, List, Optional, Set

from utils.model import Model
from utils.models import Axiom, Concept, ELFactory
from utils.tbox import TBox

logger = logging.getLogger(__name__)

el_factory = ELFactory()
top = el_factory.get_top()


class ELReasoner:
    tbox: TBox
    concepts: Set[Concept]
    concept_names: Set[Concept]

    hierarchy: DefaultDict[Concept, Set[Concept]]
    is_classified: bool

    log: logging.Logger

    def __init__(self, ontology: Any) -> None:
        self.tbox = TBox(set(Axiom(axiom) for axiom in ontology.tbox().getAxioms()))
        self.concepts = set(Concept(c) for c in ontology.getSubConcepts())
        self.concept_names = set(Concept(c) for c in ontology.getConceptNames())

        self.hierarchy = defaultdict(set)
        self.is_classified = False

        self.log = logger.getChild("ELReasoner")

    def validate_concepts(
        self,
        *concepts: str | Concept,
    ) -> List[Concept]:
        output = []
        for concept in concepts:
            if isinstance(concept, str):
                concept = el_factory.get_concept_name(concept)
            output.append(concept)

        assert (
            set(output) <= self.concepts
        ), f"Some of the concepts in {list(str(c) for c in output)} are invalid."

        return output

    def validate_concept(
        self,
        concept: str | Concept,
    ) -> Concept:
        try:
            return self.validate_concepts(concept)[0]
        except AssertionError:
            msg = f'Invalid class name {concept}. Maybe you forgot the " "? Or maybe it\'s better without them?'
            raise AssertionError(msg)

    def is_subsumed_by(
        self,
        subsumee: str | Concept,
        subsumer: str | Concept,
    ) -> bool:
        self.log.info(f"Trying to find a model for O |= {subsumee} ⊑ {subsumer}\n\n")

        subsumee, subsumer = self.validate_concepts(subsumee, subsumer)

        model = self.build_model(subsumee=subsumee, subsumer=subsumer)
        result = model.apply_rules()

        self.log_results(subsumee, subsumer, result)

        return result

    def classify(self) -> None:
        for concept in self.concept_names:
            self.fill_all_subsumers(concept)

        self.is_classified = True

    def get_subsumers(
        self,
        subsumee: str | Concept,
        print_output: bool = True,
    ) -> None:
        subsumee = self.validate_concept(subsumee)

        if not self.is_classified:
            self.fill_all_subsumers(subsumee)

        if print_output:
            self.print_subsumers(subsumee)

    def print_subsumers(self, subsumee: Concept) -> None:
        for subsumer in self.hierarchy[subsumee]:
            print(subsumer)

    def log_results(
        self,
        subsumee: Concept,
        subsumer: Concept,
        result: bool,
    ) -> None:
        msg = (
            f"{subsumee} IS subsumed by {subsumer}\n\n"
            if result
            else f"{subsumee} is NOT subsumed by {subsumer}"
        )
        self.log.info(msg)

    def build_model(
        self,
        subsumee: Concept,
        subsumer: Optional[Concept] = None,
    ) -> Model:
        if not subsumer:
            subsumer = top

        input_concepts = self.concepts | {subsumee, subsumer}
        model = Model(input_concepts=input_concepts, axioms=self.tbox.normalized)
        model.initialize_model(subsumee=subsumee, subsumer=subsumer)
        return model

    def compute_subsumers(self, subsumee: Concept) -> None:
        self.log.info(f"Computing subsumers of {subsumee}\n\n")

        model = self.build_model(subsumee=subsumee)
        model.apply_rules()

        self.hierarchy[model.subsumee] |= set(
            c for c in model.initial_individual.concepts if (c in self.concept_names)
        )

        self.log.info(f"Subsumers of {subsumee} have been added to hierarchy")

    def fill_all_subsumers(self, subsumee: Concept) -> None:
        added = set()

        if not self.hierarchy.get(subsumee):
            self.compute_subsumers(subsumee=subsumee)

        for subsumer in self.hierarchy[subsumee]:
            if not self.hierarchy.get(subsumer):
                self.compute_subsumers(subsumee=subsumer)

            added |= self.hierarchy[subsumer] - self.hierarchy[subsumee]

        self.hierarchy[subsumee] |= added
        while added:
            self.fill_all_subsumers(subsumee)
