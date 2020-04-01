"""
    Support function for loading test datasets
"""
import os
import os.path as op
from os import makedirs


def load_test_data(name, path_to=""):
    """ Load test data, template and needed scripts """

    data_dir = {
        "AtlasBREX": "xtffSJfiBqCQZWi",
        "NMT_v1.2": "8LXLzFAE89x28Lp",
        "NMT_FSL": "ajAtB7qgaPAmKyJ",
        "inia19": "WZo9wZdreTMwfQA",
        "data_test_macapype": "Fn8a57PpQWPacZR"
    }

    if path_to == "":
        path_to = op.expanduser("~")

    assert op.exists(path_to), "Breaking, {} do not exist".format(path_to)

    data_dirpath = op.join(path_to, "data_macapype")

    try:
        makedirs(data_dirpath)
    except OSError:
        print("data_dirpath {} already exists".format(data_dirpath))

    data_path = op.join(data_dirpath, name)

    if op.exists(data_path):
        print("{} Already exists, skipping download".format(data_path))
        return data_path

    data_zip = op.join(data_dirpath, "{}.zip".format(name))

    if not op.exists(data_zip):

        print("Download {}".format(data_zip))

        assert name in data_dir.keys(),\
            "Error, {} not found in data_dict".format(name)
        oc_path = "https://cloud.int.univ-amu.fr/index.php/s/{}/download"\
            .format(data_dir[name])
        os.system("wget -O {} --no-check-certificate  --content-disposition\
            {}".format(data_zip, oc_path))

    assert op.exists(data_zip),\
        "Error, data_zip = {} not found ".format(data_zip)

    print("Unzip {} to {}".format(data_zip, data_path))
    os.system("unzip -o {} -d {}".format(data_zip, data_path))
    os.remove(data_zip)

    assert op.exists(data_path)

    return data_path
