from typing import Dict, List, Optional

# '%' matches wildcard characters in a postgres 'like' statement
wildcard = "%"

facets: Dict[str, Dict[str, List[str]]] = {
    "cytof": {
        "source": [
            f"source_{wildcard}.fcs",
            "spike_in_fcs.fcs",
            "normalized_and_debarcoded.fcs",
            "processed.fcs",
        ],
        "cell counts": [
            "cell_counts_assignment.csv",
            "cell_counts_compartment.csv",
            "cell_counts_profiling.csv",
        ],
        "labeled source": ["source.fcs"],
        "analysis results": ["analysis.zip", "results.zip"],
        "key": ["assignment.csv", "compartment.csv", "profiling.csv"],
    },
    "wes": {
        "source": [
            f"reads_{wildcard}.bam",
            f"r1_{wildcard}.fastq.gz",
            f"r2_{wildcard}.fastq.gz",
        ],
        "germline": ["vcfcompare.txt", "optimalpurityvalue.txt"],
        "clonality": ["clonality_pyclone.tsv"],
        "copy number": ["copynumber_cnvcalls.txt", "copynumber_cnvcalls.txt.tn.tsv"],
        "neoantigen": ["MHC_Class_I_all_epitopes.tsv"],
    },
    "rnaseq": {},
}


# def get_facets() -> List[str]:
#     return list(facets.keys())


# def get_facet_filenames(facet: str, subfacet: Optional[str] = None) -> List[str]:
#     assert facet in facets, f"No facets found for {facet}"
#     subfacets = facets[facet]
#     if subfacets and subfacet:
#         assert subfacet in subfacets
#         return subfacets[subfacet]
