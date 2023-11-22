#!/usr/bin/env python3

import logging
import sys

from utils import gateway
from utils.reasoner import ELReasoner


def main(file_name: str, class_name: str) -> None:
    log_level = logging.INFO
    logging.basicConfig(
        filename="dl-reasoning.log", filemode="w", encoding="utf-8", level=log_level
    )
    logger = logging.getLogger(__name__)

    parser = gateway.getOWLParser()

    logger.info("Loading the ontology ...")
    ontology = parser.parseFile(file_name)
    logger.info("Ontology loaded")

    logger.info("Converting to binary conjunctions ...")
    gateway.convertToBinaryConjunctions(ontology)

    el_reasoner = ELReasoner(ontology)

    el_reasoner.get_concept_hierarchy(concept_name=class_name, upwards=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
