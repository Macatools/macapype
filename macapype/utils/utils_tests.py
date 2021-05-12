"""
    Support function for loading test datasets
"""
import os
import os.path as op

import shutil
import json
import subprocess


def _download_data_zip(data_zip, name):

    json_data = op.join(op.dirname(op.abspath(__file__)),
                        "data_test_servers.json")

    data_dict = json.load(open(json_data))

    for key, cloud_elem in data_dict.items():
        print(key)

        data_dir = cloud_elem["data_dir"]

        if name not in data_dir.keys():

            print("{} not found in {}".format(name, key))
            continue

        server = cloud_elem["server"]

        if "cloud_format" in list(cloud_elem.keys()):
            oc_path = cloud_elem["cloud_format"].format(server, data_dir[name])
        elif "cloud_format_3" in list(cloud_elem.keys()):
            oc_path = cloud_elem["cloud_format_3"].format(server,
                                                          data_dir[name], name)

        cmd = 'wget --no-check-certificate  \
            --content-disposition  {} -O {} '.format(oc_path, data_zip)

        val = subprocess.call(cmd.split())

        if val:
            print("Error with {} for {}".format(cmd, key))
            continue

        if op.exists(data_zip):
            print(os.listdir(op.split(data_zip)[0]))

            print("Ok for download {} with {}".format(data_zip, key))
            print("Quitting download function")

            return True

    assert op.exists(data_zip),\
        "Error, data_zip = {} not found ".format(data_zip)

    return False


def load_test_data(name, path_to=""):
    """ Load test data, template and needed scripts """

    if path_to == "":
        path_to = op.expanduser("~")

    assert op.exists(path_to), "Breaking, {} do not exist".format(path_to)

    data_dirpath = op.join(path_to, "data_macapype")

    try:
        os.makedirs(data_dirpath)
    except OSError:
        print("data_dirpath {} already exists".format(data_dirpath))

    data_path = op.join(data_dirpath, name)

    if op.exists(data_path):
        print("{} Already exists, skipping download".format(data_path))
        return data_path

    data_zip = op.join(data_dirpath, "{}.zip".format(name))

    if not op.exists(data_zip):

        print("Download {}".format(data_zip))

        val = _download_data_zip(data_zip, name)

        assert val, "Error, cannot download {}".format(data_zip)

    assert op.exists(data_zip), "Error, cannot find {}".format(data_zip)

    print("Unzip {} to {}".format(data_zip, data_path))
    os.system("unzip -o {} -d {}".format(data_zip, data_path))
    os.remove(data_zip)

    assert op.exists(data_path), "Error, cannot find {}".format(data_path)

    return data_path


def format_template(data_path, template_name):

    import json

    json_template = op.join(op.dirname(op.abspath(__file__)),
                            "templates.json")

    template_path_dict = json.load(open(json_template))

    assert template_name in template_path_dict.keys(), \
        "Error, could not find template formating for {} in {}".format(
            template_name, template_path_dict.keys())
    template_dict = template_path_dict[template_name]
    print("Found template formating for {}:".format(template_name))
    print(template_dict)

    for key, value in template_dict.items():
        template_file = op.join(data_path, value)
        assert op.exists(template_file), "Error, file {} is missing".format(
            template_file)

        template_dict[key] = template_file

    return template_dict


def make_tmp_dir():
    tmp_dir = "/tmp/test_macapype"
    if op.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    os.chdir(tmp_dir)

    return tmp_dir
