#!/usr/bin/env python3

import sys

from utils.java_gateway import gateway
from utils.reasoner import ELReasoner


def main(file_name="dutch-pancakes.owx", class_name=None, *arg):
    parser = gateway.getOWLParser()

    print("Loading the ontology ...")
    ontology = parser.parseFile(file_name)
    print("Ontology loaded")

    print("Converting to binary conjunctions ...")
    gateway.convertToBinaryConjunctions(ontology)

    # get the TBox axioms
    tbox = ontology.tbox()
    axioms = tbox.getAxioms()
    concept_names = ontology.getConceptNames()

    # reason
    el_reasoner = ELReasoner(axioms, concept_names)
    el_reasoner.compute_hierarchy()
    el_reasoner.print_hierarchy()


if __name__ == "__main__":
    main(*sys.argv[1:])
