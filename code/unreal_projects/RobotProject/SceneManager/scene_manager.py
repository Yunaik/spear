import os
import sys
import getopt
import json
import urllib.request
import shutil
from concurrent import futures
from tqdm import tqdm

CDN_API = "https://kloudsim-usa-cos.kujiale.com/Samples_i/dataset-repo/"
# CDN_API = 'https://kloudsim-nj-cos.kujiale.com/interiorsim/dataset-repo/'

PROJECT_SAVED_FOLDER = os.path.join(os.path.dirname(__file__), "../Saved")
TEMP_FOLDER = os.path.join(PROJECT_SAVED_FOLDER, "Temp")
VERSION_INFO_FOLDER = os.path.join(PROJECT_SAVED_FOLDER, "VersionInfo")


def create_folder(folder_path):
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    except:
        pass


# create folder
create_folder(PROJECT_SAVED_FOLDER)
create_folder(TEMP_FOLDER)
create_folder(VERSION_INFO_FOLDER)


def check_update_version_info(local_version_info, remote_version_info):
    if os.path.exists(local_version_info) and os.path.exists(remote_version_info):
        with open(local_version_info) as f:
            local_data = json.load(f)
        with open(remote_version_info) as f:
            remote_data = json.load(f)
        if local_data["ETag"] == remote_data["ETag"]:
            return False
    return True


def check_updade_version(local_version_info, version):
    if os.path.exists(local_version_info):
        with open(local_version_info) as f:
            local_data = json.load(f)
            if not local_data["Version"] == version:
                return True
            else:
                return False
    return True


def download_file_from_url(url, local_path):
    urllib.request.urlretrieve(url, local_path)
    if os.path.exists(local_path):
        return True
    else:
        return False


def get_scene_config(virtualworld_id, version):
    scene_meta_url = (
        CDN_API
        + "scenes/"
        + virtualworld_id
        + "/"
        + version
        + "/ConfigMeta_{}.json".format(virtualworld_id)
    )
    scene_meta_local = os.path.join(
        TEMP_FOLDER, virtualworld_id, "ConfigMeta_{}.json".format(virtualworld_id)
    )
    create_folder(os.path.join(TEMP_FOLDER, virtualworld_id))
    if download_file_from_url(scene_meta_url, scene_meta_local):
        with open(scene_meta_local) as f:
            return json.load(f)
    return None


def deal_scene_file(remote_url, local_path, dst_path):
    download_file_from_url(remote_url, local_path)
    if os.path.exists(local_path):
        if os.path.exists(dst_path):
            shutil.rmtree(dst_path)
        shutil.unpack_archive(local_path, dst_path)
        if os.path.isdir(dst_path):
            return True
    return False


def download_scenes(virtualworld_id, version, scene_config_data, is_force_update):
    local_version_info_folder = os.path.join(VERSION_INFO_FOLDER, "scenes")
    create_folder(local_version_info_folder)
    version_scene_info_name = "version_info_scene_{}.json".format(virtualworld_id)
    local_version_info = os.path.join(
        local_version_info_folder, version_scene_info_name
    )
    remote_version_info_url = (
        CDN_API
        + "scenes/"
        + virtualworld_id
        + "/"
        + version
        + "/"
        + version_scene_info_name
    )
    remote_version_info = os.path.join(TEMP_FOLDER, version_scene_info_name)
    download_file_from_url(remote_version_info_url, remote_version_info)
    if not is_force_update:
        if not is_force_update:
            if not check_update_version_info(local_version_info, remote_version_info):
                return True

    anim_url = (
        CDN_API
        + "scenes/"
        + virtualworld_id
        + "/"
        + version
        + "/"
        + scene_config_data["animation"]
    )
    anim_local = os.path.join(TEMP_FOLDER, scene_config_data["animation"])
    anim_dst = os.path.join(
        os.path.dirname(__file__),
        "../Content/Scene/",
        scene_config_data["animation"].replace(".zip", ""),
    )
    is_anim_ok = deal_scene_file(anim_url, anim_local, anim_dst)

    arch_url = (
        CDN_API
        + "scenes/"
        + virtualworld_id
        + "/"
        + version
        + "/"
        + scene_config_data["architecture"]
    )
    arch_local = os.path.join(TEMP_FOLDER, scene_config_data["architecture"])
    arch_dst = os.path.join(
        os.path.dirname(__file__),
        "../Content/Scene/Meshes",
        scene_config_data["architecture"].replace(".zip", ""),
    )
    is_arch_ok = deal_scene_file(arch_url, arch_local, arch_dst)

    mat_url = (
        CDN_API
        + "scenes/"
        + virtualworld_id
        + "/"
        + version
        + "/"
        + scene_config_data["materialinst"]
    )
    mat_local = os.path.join(TEMP_FOLDER, scene_config_data["materialinst"])
    mat_dst = os.path.join(
        os.path.dirname(__file__),
        "../Content/Scene/",
        scene_config_data["materialinst"].replace(".zip", ""),
    )
    is_mat_ok = deal_scene_file(mat_url, mat_local, mat_dst)

    map_folder = os.path.join(os.path.dirname(__file__), "../Content/Maps")
    create_folder(map_folder)
    umap_local = os.path.join(map_folder, scene_config_data["map"])
    download_file_from_url(
        CDN_API
        + "scenes/"
        + virtualworld_id
        + "/"
        + version
        + "/"
        + scene_config_data["map"],
        umap_local,
    )
    is_umap_ok = False
    if os.path.exists(umap_local):
        is_umap_ok = True

    # move versioninfo file
    if is_umap_ok and is_anim_ok and is_arch_ok and is_mat_ok:
        if os.path.exists(local_version_info):
            os.remove(local_version_info)
        shutil.move(remote_version_info, local_version_info)
        # remove temp file
        if os.path.exists(anim_local):
            os.remove(anim_local)
        if os.path.exists(arch_local):
            os.remove(arch_local)
        if os.path.exists(mat_local):
            os.remove(mat_local)
        return True

    return False


def deal_asset_file(content):
    try:
        asset_url = content.get("asset_url")
        asset_local = content.get("asset_local")
        asset_dst = content.get("asset_dst")
        version_info_url = content.get("version_info_url")
        version_info_local = content.get("version_info_local")
        version_info_dst = content.get("version_info_dst")
        download_file_from_url(version_info_url, version_info_local)
        if os.path.exists(asset_dst):
            if not check_update_version_info(version_info_dst, version_info_local):
                if os.path.exists(version_info_local):
                    os.remove(version_info_local)
                return True
        if os.path.exists(asset_local):
            os.remove(asset_local)
        download_file_from_url(asset_url, asset_local)
        if os.path.exists(asset_local):
            if ".zip" in asset_local:
                if os.path.exists(asset_dst):
                    shutil.rmtree(asset_dst)
                shutil.unpack_archive(asset_local, asset_dst)
                if os.path.isdir(asset_dst):
                    if os.path.exists(version_info_dst):
                        os.remove(version_info_dst)
                    shutil.move(version_info_local, version_info_dst)
                    if os.path.exists(asset_local):
                        os.remove(asset_local)
                    return True
            else:
                if os.path.exists(version_info_dst):
                    os.remove(version_info_dst)
                shutil.move(version_info_local, version_info_dst)
                return True
    except:
        pass
    return False


def mult_down(contents):
    is_ok = True
    is_appear = False
    with futures.ProcessPoolExecutor() as pool:
        for result in tqdm(pool.map(deal_asset_file, contents), total=len(contents)):
            if not result and not is_appear:
                is_appear = True
                is_ok = False
    return is_ok


def download_assets(
    virtualworld_id, version, is_down_ddc, scene_config_data, is_force_update
):
    local_version_info_folder = os.path.join(VERSION_INFO_FOLDER, "assets")
    mat_version_info_folder = os.path.join(local_version_info_folder, "materials")
    furniture_version_info_folder = os.path.join(local_version_info_folder, "furniture")
    phys_furniture_version_info_folder = os.path.join(
        local_version_info_folder, "phys_furniture"
    )
    ddc_version_info_folder = os.path.join(local_version_info_folder, "ddc")
    create_folder(mat_version_info_folder)
    create_folder(furniture_version_info_folder)
    create_folder(phys_furniture_version_info_folder)
    if is_down_ddc:
        create_folder(ddc_version_info_folder)

    mat_down_body = []
    for materialid in scene_config_data["material"]:
        dic_curr = {}
        dic_curr["asset_url"] = (
            CDN_API
            + "assets/material/"
            + materialid
            + "/"
            + version
            + "/"
            + materialid
            + ".zip"
        )
        dic_curr["asset_local"] = os.path.join(TEMP_FOLDER, materialid + ".zip")
        dic_curr["asset_dst"] = os.path.join(
            os.path.dirname(__file__), "../Content/Scene/Materials", materialid
        )
        dic_curr["version_info_url"] = (
            CDN_API
            + "assets/material/"
            + materialid
            + "/"
            + version
            + "/"
            + "version_info_"
            + materialid
            + ".json"
        )
        dic_curr["version_info_local"] = os.path.join(
            TEMP_FOLDER, "version_info_" + materialid + ".json"
        )
        dic_curr["version_info_dst"] = os.path.join(
            mat_version_info_folder, "version_info_" + materialid + ".json"
        )
        mat_down_body.append(dic_curr)
    print("update {} material".format(virtualworld_id))
    is_mat_ok = mult_down(mat_down_body)

    furniture_down_body = []
    for meshid in scene_config_data["mesh"]:
        dic_curr = {}
        dic_curr["asset_url"] = (
            CDN_API
            + "assets/furniture/"
            + meshid
            + "/"
            + version
            + "/"
            + meshid
            + ".zip"
        )
        dic_curr["asset_local"] = os.path.join(TEMP_FOLDER, meshid + ".zip")
        dic_curr["asset_dst"] = os.path.join(
            os.path.dirname(__file__), "../Content/Scene/Meshes/Furniture", meshid
        )
        dic_curr["version_info_url"] = (
            CDN_API
            + "assets/furniture/"
            + meshid
            + "/"
            + version
            + "/"
            + "version_info_"
            + meshid
            + ".json"
        )
        dic_curr["version_info_local"] = os.path.join(
            TEMP_FOLDER, "version_info_" + meshid + ".json"
        )
        dic_curr["version_info_dst"] = os.path.join(
            phys_furniture_version_info_folder, "version_info_" + meshid + ".json"
        )
        furniture_down_body.append(dic_curr)
    print("update {} furniture".format(virtualworld_id))
    is_fur_ok = mult_down(furniture_down_body)

    phys_furniture_down_body = []
    for meshid in scene_config_data["mesh"]:
        dic_curr = {}
        dic_curr["asset_url"] = (
            CDN_API
            + "assets/phys_furniture/"
            + meshid
            + "/"
            + version
            + "/"
            + meshid
            + ".zip"
        )
        dic_curr["asset_local"] = os.path.join(TEMP_FOLDER, meshid + ".zip")
        dic_curr["asset_dst"] = os.path.join(
            os.path.dirname(__file__),
            "../Content/Scene/Meshes/PhysicalFurniture",
            meshid,
        )
        dic_curr["version_info_url"] = (
            CDN_API
            + "assets/phys_furniture/"
            + meshid
            + "/"
            + version
            + "/"
            + "version_info_"
            + meshid
            + ".json"
        )
        dic_curr["version_info_local"] = os.path.join(
            TEMP_FOLDER, "version_info_" + meshid + ".json"
        )
        dic_curr["version_info_dst"] = os.path.join(
            furniture_version_info_folder, "version_info_" + meshid + ".json"
        )
        phys_furniture_down_body.append(dic_curr)
    print("update {} phys_furniture".format(virtualworld_id))
    is_phys_fur_ok = mult_down(phys_furniture_down_body)

    if is_down_ddc:
        ddc_down_body = []
        for ddc_path in scene_config_data["DDC"]:
            ddc_only_path = ddc_path.replace(".udd", "")
            ddc_array = ddc_path.split("/")
            ddc_name = ddc_array[len(ddc_array) - 1]
            dic_curr = {}
            dic_curr["asset_url"] = (
                CDN_API + "assets/ddc/" + ddc_only_path + "/" + version + "/" + ddc_name
            )
            dic_curr["asset_local"] = os.path.join(
                os.path.dirname(__file__), "../DerivedDataCache", ddc_path
            )
            if not os.path.exists(os.path.dirname(dic_curr["asset_local"])):
                try:
                    os.makedirs(dic_curr["asset_local"])
                except:
                    pass
            dic_curr["asset_dst"] = ""
            dic_curr["version_info_url"] = (
                CDN_API
                + "assets/ddc/"
                + ddc_only_path
                + "/"
                + version
                + "/"
                + "version_info_"
                + ddc_name.replace(".udd", "")
                + ".json"
            )
            dic_curr["version_info_local"] = os.path.join(
                TEMP_FOLDER, "version_info_" + ddc_name.replace(".udd", "") + ".json"
            )
            dic_curr["version_info_dst"] = os.path.join(
                ddc_version_info_folder,
                "version_info_" + ddc_name.replace(".udd", "") + ".json",
            )
            ddc_down_body.append(dic_curr)
        print("update {} ddc".format(virtualworld_id))
        is_ddc_ok = mult_down(ddc_down_body)
        return is_mat_ok and is_fur_ok and is_phys_fur_ok and is_ddc_ok
    else:
        return is_mat_ok and is_fur_ok and is_phys_fur_ok


def download_single_virtualworld(
    virtualworld_id, version, is_down_ddc, is_force_update
):
    # get scene meta
    scene_config_data = get_scene_config(virtualworld_id, version)
    # download assets
    is_assets_ready = download_assets(
        virtualworld_id, version, is_down_ddc, scene_config_data, is_force_update
    )
    # download scenes
    is_scene_ready = download_scenes(
        virtualworld_id, version, scene_config_data, is_force_update
    )

    update_log = os.path.join(PROJECT_SAVED_FOLDER, "UpdateLog")
    if not os.path.exists(update_log):
        os.makedirs(update_log)

    log = os.path.join(update_log, virtualworld_id + "_faild.txt")
    if is_assets_ready and is_scene_ready:
        if os.path.exists(log):
            os.remove(log)
        print("download {} success".format(virtualworld_id))
        return True
    else:
        with open(log, "w") as f:
            f.writelines(
                "Please update {} again. assset is {} and scene is {}".format(
                    virtualworld_id, is_assets_ready, is_scene_ready
                )
            )
        print(
            "Please update {} again. assset is {} and scene is {}".format(
                virtualworld_id, is_assets_ready, is_scene_ready
            )
        )
        return False


def print_help():
    print(
        "scene_manager.py -i <option> -v <version> -d <option is_download_ddc> -f <option is_force_upadte>\ne.g:scene_manager.py -v v1"
    )
    sys.exit(2)


if __name__ == "__main__":
    version = ""
    virtualworld_id = ""
    is_down_ddc = False
    is_force_update = False

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "h:i:v:d:f:",
            ["help=", "infile=", "version=", "downDDC=", "forceUpade="],
        )
    except getopt.GetoptError:
        print_help()

    for opt, arg in opts:
        if opt == ("-h", "--help"):
            print_help()
        elif opt in ("-i", "--infile"):
            virtualworld_id = arg
        elif opt in ("-v", "--version"):
            if "v" in arg:
                version = arg
        elif opt in ("-f", "--forceUpade"):
            if arg in ["true", "True"]:
                is_force_update = True
        elif opt in ("-d", "--downDDC"):
            if arg in ["true", "True"]:
                is_down_ddc = True

    if version == "":
        print(
            "set version correct. please select version form SceneManage/Data/dataset-repo-update.log"
        )
        print_help()

    if virtualworld_id == "":
        virtualworld_ids_file = os.path.join(
            os.path.dirname(__file__), "Data/virtualworld-ids.json"
        )
        if os.path.exists(virtualworld_ids_file):
            with open(virtualworld_ids_file) as f:
                for id in json.load(f):
                    download_single_virtualworld(
                        id, version, is_down_ddc, is_force_update
                    )
    else:
        download_single_virtualworld(
            virtualworld_id, version, is_down_ddc, is_force_update
        )
