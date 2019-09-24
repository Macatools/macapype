"""
Support function for loading test datasets
"""
import os


def load_test_data(name):
    """load test data"""
    data_dir = {"data_nii": "STtqD3Y4ZZYqpTm",
                "data_con": "kEXrxPs4DgAJaLs",
                "data_gather": "5SQpidYQJXqij6F",
                "data_con_meg": "yAbqiq5WqAzSRkC",
                "data_inv_ts": "HT85yik8iR5W5rF"}

    data_path = os.path.join(os.getcwd(), name)
    data_zip = os.path.join(os.getcwd(), "{}.zip".format(name))

    if os.path.exists(data_path):
        return data_path

    if not os.path.exists(data_zip):

        assert name in data_dir.keys(),\
            "Error, {} not found in data_dict".format(name)
        oc_path = "https://cloud.int.univ-amu.fr/index.php/s/{}/download"\
            .format(data_dir[name])
        os.system("wget -O {} --no-check-certificate  --content-disposition\
            {}".format(data_zip, oc_path))

    assert os.path.exists(data_zip),\
        "Error, data_zip = {} not found ".format(data_zip)

    os.system("unzip -o {}".format(data_zip))

    data_path = os.path.join(os.getcwd(), name)

    assert os.path.exists(data_path)

    return data_path
