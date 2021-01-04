"""
    Support function for loading test datasets
"""
import os
import os.path as op
from os import makedirs
import shutil


def load_test_data(name, path_to=""):
    """ Load test data, template and needed scripts """

    data_dict = {
        "INT": {
            "server": "cloud.int.univ-amu.fr",
            "data_dir": {
                "NMT_v1.2": "QBTrmKNDrNs5E49",
                "NMT_v1.2.hemi": "SMPYKkrpiP8XrFT",
                "NMT_FSL": "ajAtB7qgaPAmKyJ",
                "inia19": "WZo9wZdreTMwfQA",
                "marmotemplate": "5xzm7DJD9kB99gG",
                "haiko89_template": "N9yXkSgXNbKF26z",
                "data_test_macaque": "SgG7bBMXao9Kfon",
                "data_test_sphinx_macaque": "f6C48Y3QqJfD9wM",
                "data_test_marmo": "pW4nQr46QSzSysg"},
            "cloud_format": "https://{}/index.php/s/{}/download"},

        "AMUBOX": {
            "server": "https://amubox.univ-amu.fr",
            "data_dir": {
                "data_test_macaque": "RDxdxzmX89xcABG",
                "data_test_sphinx_macaque": "RkWbC2gmbn4ytK3",
                "NMT_v1.2": "5YnwNf3Jr7Qsc8H"},
            "cloud_format": "{}/public.php?service=files&t={}&download"}}

    def _download_data_zip(data_zip, name):

        for key, cloud_elem in data_dict.items():
            print(key)

            data_dir = cloud_elem["data_dir"]

            if name not in data_dir.keys():

                print("{} not found in {}".format(name, key))
                continue

            server = cloud_elem["server"]
            oc_path = cloud_elem["cloud_format"].format(server, data_dir[name])

            os.system("wget --no-check-certificate  \
                --content-disposition \"{}\" -O {} ".format(oc_path, data_zip))

            if op.exists(data_zip):
                print("Ok for download {} with {}, \
                      quitting download function".format(data_zip, key))
                return

        assert op.exists(data_zip),\
            "Error, data_zip = {} not found ".format(data_zip)

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

        _download_data_zip(data_zip, name)

    print("Unzip {} to {}".format(data_zip, data_path))
    os.system("unzip -o {} -d {}".format(data_zip, data_path))
    os.remove(data_zip)

    assert op.exists(data_path)

    return data_path


def format_template(data_path, template_name):

    import json

    json_template = op.join(os.path.dirname(os.path.abspath(__file__)),
                            "templates.json")

    template_path_dict = json.load(open(json_template))

    assert template_name in template_path_dict.keys(), \
        "Error, could not find template formating for {} in {}".format(
            template_name, template_path_dict.keys())
    template_dict = template_path_dict[template_name]
    print("Found template formating for {}:".format(template_name))
    print(template_dict)

    for key, value in template_dict.items():
        template_dict[key] = op.join(data_path, value)

    return template_dict


def make_tmp_dir():
    tmp_dir = "/tmp/test_macapype"
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    os.chdir(tmp_dir)

    return tmp_dir
