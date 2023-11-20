from collections import defaultdict

from utils.java_gateway import gateway
from utils.models import Axiom, ConceptName, ELFactory
from utils.tbox import TBox

el_factory = ELFactory(gateway.getELFactory())


class ELReasoner:
    def __init__(self, tbox_axioms: any, concept_names: any) -> None:
        tbox_axioms = set(Axiom(axiom) for axiom in tbox_axioms)
        self.tbox = TBox(tbox_axioms, el_factory)
        self.hierarchy = defaultdict(set)
        self.concept_names = set(ConceptName(concept) for concept in concept_names)

    def compute_hierarchy(self):
        for concept in self.concept_names:
            # add top and the class name
            self.hierarchy[str(concept)] |= {el_factory.get_top(), concept}

    def print_hierarchy(self):
        for key, value in self.hierarchy.items():
            print(key, end="\n")
            for c in value:
                print(f"{'':<4}{c}")
