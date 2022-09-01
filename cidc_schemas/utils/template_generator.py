from os import path
from openpyxl import load_workbook
from typing import Callable, List, Tuple, Union

from ..template import Template
from ..template_writer import XlTemplateWriter


wes_analysis_template = Template.from_type("wes_analysis")


def write_wes_analysis_batch(
    output_folder: str,
    protocol_identifier: str,
    folder: Union[str, Callable[[str], str]],
    normal_tumor_pairs: List[Tuple[str]],
    path_generator: Callable[[str], str] = None,
):
    """
    Given a set of tumor-normal pairs, generate a template for each pair with the given protocol identifier

    Parameters
    ----------
    output_folder: str
        the path to the output folder to put all of the filled templates in
    folder : str, Callable[str -> str]
        the value for `folder` in the #preamble
        if string, a constant across all templates
            default: lambda tumor: folder
        if Callable, returns the `folder` value given the run id
    normal_tumor_pairs : Tuple[str, str]
        the normal and tumor CIMAC IDs; normal, then tumor
        the tumor id is used as the run id
    path_generator : Callable[str -> str]
        default: lambda id: os.path.join(output_folder, f"{id}_template.xlsx")
        takes the run id and returns the path to store the filled template
    """
    if isinstance(folder, Callable):
        folder_func = folder
    else:
        # use a constant function to preserve structure
        folder_func = lambda _: folder

    if path_generator is None:
        path_generator = lambda id: path.join(output_folder, f"{id}_template.xlsx")

    for normal_cimac_id, tumor_cimac_id in normal_tumor_pairs:
        write_wes_analysis_template(
            path_generator(tumor_cimac_id),
            protocol_identifier,
            folder_func(tumor_cimac_id),  # i.e. the run id
            normal_cimac_id,
            tumor_cimac_id,
        )


def write_wes_analysis_template(
    outfile_path: str,
    protocol_identifier: str,
    folder: str,
    normal_cimac_id: str,
    tumor_cimac_id: str,
):
    """
    Given a tumor-normal pairing, generate a template with the given protocol identifier

    Parameters
    ----------
    output_path: str
        the path to the output excel
    folder : str, Callable[str -> str]
        the value for `folder` in the #preamble
    normal_cimac_id, tumor_cimac_id : str, str
        the normal and tumor CIMAC IDs
        the tumor id is used as the run id
    """
    XlTemplateWriter().write(outfile_path, wes_analysis_template)

    wb = load_workbook(outfile_path)

    # set the #preamble values
    wb["WES Analysis"]["C2"] = protocol_identifier
    wb["WES Analysis"]["C3"] = folder

    # set the #data values
    wb["WES Analysis"]["B7"] = tumor_cimac_id
    wb["WES Analysis"]["C7"] = normal_cimac_id
    wb["WES Analysis"]["D7"] = tumor_cimac_id

    wb.save(outfile_path)
