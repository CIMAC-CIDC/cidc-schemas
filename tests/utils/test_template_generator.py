from os import mkdir

from cidc_schemas.utils.template_generator import (
    write_wes_analysis_batch,
    write_wes_analysis_template,
    wes_analysis_template,
)
from cidc_schemas.template_reader import XlTemplateReader
from cidc_schemas.prism import prismify
from cidc_schemas.prism.constants import PROTOCOL_ID_FIELD_NAME


def test_write_wes_analysis_functions(tmpdir):
    mkdir(tmpdir.join("secret"))

    test_output_folder = tmpdir
    test_folder_func = lambda tumor: f"gs://{tumor}"
    test_path_generator = lambda tumor: tmpdir.join("secret").join(f"{tumor}.xlsx")

    test_output_path = tmpdir.join("/bar.xlsx")
    test_protocol_identifier = "test-id"
    test_folder = "gs://foo"
    test_normal, test_tumor = "bar", "baz"

    for i in range(3):
        if i == 0:
            write_wes_analysis_template(
                outfile_path=test_output_path,
                protocol_identifier=test_protocol_identifier,
                folder=test_folder,
                normal_cimac_id=test_normal,
                tumor_cimac_id=test_tumor,
            )
            reader, errs = XlTemplateReader.from_excel(test_output_path)
        elif i == 1:
            write_wes_analysis_batch(
                output_folder=test_output_folder,
                protocol_identifier=test_protocol_identifier,
                folder=test_folder,
                normal_tumor_pairs=[(test_normal, test_tumor)],
            )
            reader, errs = XlTemplateReader.from_excel(
                f"{test_output_folder}/{test_tumor}_template.xlsx"
            )
        elif i == 2:
            write_wes_analysis_batch(
                output_folder=test_output_folder,
                protocol_identifier=test_protocol_identifier,
                folder=test_folder_func,
                normal_tumor_pairs=[(test_normal, test_tumor)],
                path_generator=test_path_generator,
            )
            reader, errs = XlTemplateReader.from_excel(test_path_generator(test_tumor))

        assert len(errs) == 0, str(errs)

        patch_ct, files, errs = prismify(reader, wes_analysis_template)
        assert len(errs) == 0, str(errs)

        assert patch_ct.get(PROTOCOL_ID_FIELD_NAME) == test_protocol_identifier
        runs = patch_ct.get("analysis", {}).get("wes_analysis", {}).get("pair_runs", [])
        assert len(runs) == 1
        run = runs[0]
        assert run.get("run_id") == test_tumor
        assert run.get("normal", {}).get("cimac_id") == test_normal
        assert run.get("tumor", {}).get("cimac_id") == test_tumor

        for file in files:  # LocalFileUploadEntry
            if i == 2:
                assert file.local_path.startswith(test_folder_func(test_tumor))
            else:
                assert file.local_path.startswith(test_folder)
