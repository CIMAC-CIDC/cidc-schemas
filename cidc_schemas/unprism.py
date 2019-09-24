from pandas.io.json import json_normalize


def unprism_participants(json):
    """ Returns csv content as string.

    >>> print(unprism_participants({"participants": [{"arm_id": "12345", "gender": "Male", "samples":[], "cohort_id": "54321", "cimac_participant_id": "PA1", "trial_participant_id": "tPA1"}, {"race": "White", "gender":"Other", "arm_id": "12345", "samples":[], "cohort_id": "54321", "cimac_participant_id": "PA2", "trial_participant_id": "tPA2"}], "lead_organization_study_id": "test_trial_id#"}))
    ,arm_id,gender,samples,cohort_id,cimac_participant_id,trial_participant_id,race,lead_organization_study_id
    0,12345,Male,[],54321,PA1,tPA1,,test_trial_id#
    1,12345,Other,[],54321,PA2,tPA2,White,test_trial_id#
    <BLANKLINE>

    """
    return json_normalize(data=json, record_path=['participants'],
                            meta=['lead_organization_study_id']).to_csv()


def unprism_assay_samples(assay_type: str, json):
    """
    >>> print(unprism_assay_samples("cytof" ,{"assays": {"cytof": [{"records": [{"files": {"source_fcs": [{"md5_hash": "1B2M2Y8AsgTpgAmY7PhCfg==", "file_name": "cytof", "object_url": "staging_0/test/test/PA2SA1-al5/cytof/source_0.fcs", "data_format": "BINARY", "file_size_bytes": 0, "artifact_category": "Assay Artifact from CIMAC", "upload_placeholder": "e34b0f01-c980-405f-b97c-c7de4dd80ede", "uploaded_timestamp": "2019-09-23T15:40:16.307000+00:00"}], "processed_fcs": {"md5_hash": "1B2M2Y8AsgTpgAmY7PhCfg==", "file_name": "cytof", "object_url": "staging_0/test/test/PA2SA1-al5/cytof/processed.fcs", "data_format": "BINARY", "file_size_bytes": 0, "artifact_category": "Assay Artifact from CIMAC", "upload_placeholder": "c7118184-d3ce-44d7-a773-2870edfa6431", "uploaded_timestamp": "2019-09-23T15:40:19.104000+00:00"}}, "batch_id": "test", "injector": "sdf", "run_time": "7", "beads_removed": "Y", "cimac_sample_id": "test", "debarcoding_key": "dfg", "cimac_aliquot_id": "PA2SA1-al5", "acquisition_buffer": "sdf", "date_of_acquisition": "2012-12-12 00:00:00", "preprocessing_notes": "dfg", "cimac_participant_id": "test", "debarcoding_protocol": "dfg", "concatenation_version": "5", "normalization_version": "5", "average_event_per_second": 7.0}], "instrument": "sdf", "panel_name": "sdf", "assay_creator": "DFCI", "cytof_antibodies": [{"clone": "dfg", "usage": "Ignored", "cat_num": "123", "company": "dfg", "isotope": "123", "lot_num": "123", "antibody": "dfg", "dilution": "123", "stain_type": "Surface Stain"}]}]}}))
    True

    """
    return json_normalize(data=json, record_path=['assays', assay_type, "records"],
                            meta=[]).to_csv()