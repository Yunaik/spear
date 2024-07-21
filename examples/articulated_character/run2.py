#
# Copyright(c) 2022 Intel. Licensed under the MIT License <http://opensource.org/licenses/MIT>.
#

import os
import readchar
import spear
import json
import numpy as np
from scipy.spatial.transform import Rotation as R

SPACE = "ComponentSpace"
if __name__ == "__main__":

    spear.log("Initializing SPEAR instance...")

    # create SPEAR instance
    config = spear.get_config(
        user_config_files=[
            os.path.realpath(
                os.path.join(os.path.dirname(__file__), "user_config.yaml")
            )
        ]
    )
    spear.configure_system(config)
    spear_instance = spear.Instance(config)

    spear.log("Finished initializing SPEAR instance.")

    spear_instance.engine_service.begin_tick()

    # get Unreal actors and functions
    actor = spear_instance.unreal_service.find_actor_by_name(
        class_name="AActor", name="Debug/MixamoActor"
    )  # "Debug/Manny"
    poseable_mesh_component = spear_instance.unreal_service.get_component_by_type(
        class_name="UPoseableMeshComponent", actor=actor
    )

    gameplay_statics_static_class = spear_instance.unreal_service.get_static_class(
        class_name="UGameplayStatics"
    )
    poseable_mesh_component_static_class = (
        spear_instance.unreal_service.get_static_class(
            class_name="UPoseableMeshComponent"
        )
    )

    gameplay_statics_default_object = spear_instance.unreal_service.get_default_object(
        uclass=gameplay_statics_static_class
    )

    set_game_paused_func = spear_instance.unreal_service.find_function_by_name(
        uclass=gameplay_statics_static_class, name="SetGamePaused"
    )
    get_bone_transform_by_name_func = (
        spear_instance.unreal_service.find_function_by_name(
            uclass=poseable_mesh_component_static_class, name="GetBoneTransformByName"
        )
    )
    set_bone_transform_by_name_func = (
        spear_instance.unreal_service.find_function_by_name(
            uclass=poseable_mesh_component_static_class, name="SetBoneTransformByName"
        )
    )

    # the game starts paused by default, so unpause the game, because bone transforms won't visually update otherwise
    args = {"bPaused": False}
    spear_instance.unreal_service.call_function(
        uobject=gameplay_statics_default_object,
        ufunction=set_game_paused_func,
        args=args,
    )

    spear_instance.engine_service.tick()
    spear_instance.engine_service.end_tick()

    skeleton_mapping = {
        "Hips": "pelvis",
        "Spine": "spine1",
        "Spine1": "spine2",
        "Spine2": "spine3",
        "Neck": "neck",
        "Head": "head",
        "LeftShoulder": "left_collar",
        "LeftArm": "left_shoulder",
        "LeftForeArm": "left_elbow",
        "LeftHand": "left_wrist",
        "RightShoulder": "right_collar",
        "RightArm": "right_shoulder",
        "RightForeArm": "right_elbow",
        "RightHand": "right_wrist",
        "LeftUpLeg": "left_hip",
        "LeftLeg": "left_knee",
        "LeftFoot": "left_ankle",
        "LeftToeBase": "left_foot",
        "RightUpLeg": "right_hip",
        "RightLeg": "right_knee",
        "RightFoot": "right_ankle",
        "RightToeBase": "right_foot",
    }

    bone_names = [
        "Hips"
    ]  # , "LeftForeArm", "RightForeArm"] # ["head", "hand_l", "hand_r"]

    default_pose_dic = [
        {
            "BoneName": "Hips",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.7071067215818992,
                    "y": 0,
                    "z": 0,
                    "w": 0.7071068407911908,
                },
                "translation": {
                    "x": 80,
                    "y": 229.47875899076462,
                    "z": 132.6252670288086,
                },
                "scale3D": {"x": 1, "y": 0.9999999403953552, "z": 0.9999999403953552},
            },
        },
        {
            "BoneName": "Spine",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.7051044004779011,
                    "y": 0,
                    "z": 0,
                    "w": -0.7091035074857565,
                },
                "translation": {
                    "x": 80,
                    "y": 229.44682854046926,
                    "z": 138.2709885992984,
                },
                "scale3D": {"x": 1, "y": 0.9999999403953552, "z": 0.9999999403953552},
            },
        },
        {
            "BoneName": "Spine1",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.7051044040579463,
                    "y": 0,
                    "z": 0,
                    "w": 0.7091035039950714,
                },
                "translation": {
                    "x": 80,
                    "y": 229.4095767868664,
                    "z": 144.8576657982664,
                },
                "scale3D": {"x": 1, "y": 0.9999999403953552, "z": 0.9999999403953552},
            },
        },
        {
            "BoneName": "Spine2",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.7051044040579463,
                    "y": 0,
                    "z": 0,
                    "w": -0.7091035039950714,
                },
                "translation": {
                    "x": 80,
                    "y": 229.36700313531662,
                    "z": 152.38529878967677,
                },
                "scale3D": {"x": 1, "y": 0.9999999403953552, "z": 0.9999999403953552},
            },
        },
        {
            "BoneName": "Neck",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.7071067214607137,
                    "y": 0,
                    "z": 0,
                    "w": 0.7071068408430111,
                },
                "translation": {
                    "x": 80,
                    "y": 229.31910824363877,
                    "z": 160.85387947024654,
                },
                "scale3D": {"x": 1, "y": 0.9999999403953552, "z": 0.9999999403953552},
            },
        },
        {
            "BoneName": "Head",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.7071067214953963,
                    "y": 0,
                    "z": 0,
                    "w": -0.7071068408776937,
                },
                "translation": {
                    "x": 80,
                    "y": 228.1601493412151,
                    "z": 166.85277980666302,
                },
                "scale3D": {"x": 1, "y": 0.9999999403953552, "z": 0.9999999403953552},
            },
        },
        {
            "BoneName": "LeftShoulder",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.6967298633104387,
                    "y": -0.6996522607452008,
                    "z": -0.11416146368506233,
                    "w": 0.1096420166488695,
                },
                "translation": {
                    "x": 83.41461372375488,
                    "y": 229.3080742578532,
                    "z": 159.7284148038886,
                },
                "scale3D": {"x": 1, "y": 1.0000005364417675, "z": 0.9999995231628667},
            },
        },
        {
            "BoneName": "LeftArm",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.7107923348141755,
                    "y": 0.7033267197188199,
                    "z": 0.009991751704588991,
                    "w": -0.0024386465203900237,
                },
                "translation": {
                    "x": 90.24416196866477,
                    "y": 229.2860031335309,
                    "z": 157.48152269116457,
                },
                "scale3D": {
                    "x": 1.000000238418579,
                    "y": 0.9999997615809697,
                    "z": 1.000000238418263,
                },
            },
        },
        {
            "BoneName": "LeftForeArm",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.7179747067544067,
                    "y": -0.6960469370092833,
                    "z": -0.0040329400655307645,
                    "w": -0.0038363179412192845,
                },
                "translation": {
                    "x": 114.44265771374856,
                    "y": 229.5438048182398,
                    "z": 157.05732593856948,
                },
                "scale3D": {
                    "x": 1.000000238418579,
                    "y": 1.0000002384180142,
                    "z": 0.999999880790309,
                },
            },
        },
        {
            "BoneName": "LeftHand",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.6966546004626187,
                    "y": 0.7150015800330195,
                    "z": -0.05216605298367744,
                    "w": -0.026903738042486795,
                },
                "translation": {
                    "x": 136.02738790020004,
                    "y": 230.2133797729067,
                    "z": 157.0549894939195,
                },
                "scale3D": {
                    "x": 1.000000357627897,
                    "y": 1.0000003576273322,
                    "z": 0.9999995827671206,
                },
            },
        },
        {
            "BoneName": "RightShoulder",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.6989870405515085,
                    "y": -0.697397417602062,
                    "z": -0.11380603044012103,
                    "w": -0.11000975637860969,
                },
                "translation": {
                    "x": 76.58539628982544,
                    "y": 229.3301419380826,
                    "z": 159.72841658499974,
                },
                "scale3D": {"x": 1, "y": 1.0000005364417675, "z": 0.9999997019767903},
            },
        },
        {
            "BoneName": "RightArm",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.7093669661755728,
                    "y": 0.7047753669109114,
                    "z": 0.008773126250118628,
                    "w": 0.0036361724729830898,
                },
                "translation": {
                    "x": 69.75583741241736,
                    "y": 229.3522095584003,
                    "z": 157.48142401495494,
                },
                "scale3D": {
                    "x": 0.999999463558197,
                    "y": 0.9999999999996767,
                    "z": 0.9999995231629093,
                },
            },
        },
        {
            "BoneName": "RightForeArm",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.7182595637754069,
                    "y": -0.6957644188474786,
                    "z": -0.0028253809577160893,
                    "w": 0.002662655335583513,
                },
                "translation": {
                    "x": 45.557349743041605,
                    "y": 229.5109059759075,
                    "z": 157.05730010186284,
                },
                "scale3D": {
                    "x": 0.9999998211858738,
                    "y": 0.9999999999996767,
                    "z": 0.9999997615813747,
                },
            },
        },
        {
            "BoneName": "RightHand",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.6961633632258456,
                    "y": 0.7158017841479857,
                    "z": -0.05016294933886456,
                    "w": 0.021634600254434484,
                },
                "translation": {
                    "x": 23.9726505436756,
                    "y": 230.19788196562752,
                    "z": 157.05504788619047,
                },
                "scale3D": {
                    "x": 1.0000002980229468,
                    "y": 0.9999995827671633,
                    "z": 1.0000002384184192,
                },
            },
        },
        {
            "BoneName": "LeftUpLeg",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.023060813737504567,
                    "y": 0.7011939182850241,
                    "z": 0.7122124976505875,
                    "w": 0.023423191970217805,
                },
                "translation": {
                    "x": 86.62018060684204,
                    "y": 229.0315810373442,
                    "z": 123.80840632629685,
                },
                "scale3D": {
                    "x": 1.0000001192092896,
                    "y": 0.9999997615814316,
                    "z": 1.000000417232485,
                },
            },
        },
        {
            "BoneName": "LeftLeg",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.008287307297416936,
                    "y": -0.6992254179396148,
                    "z": -0.7148043003246665,
                    "w": -0.008363473099921715,
                },
                "translation": {
                    "x": 89.36916939632484,
                    "y": 229.68245784628613,
                    "z": 87.73164444009244,
                },
                "scale3D": {
                    "x": 0.9999997615813783,
                    "y": 0.9999999999999538,
                    "z": 1.000000238418476,
                },
            },
        },
        {
            "BoneName": "LeftFoot",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.01992400896590751,
                    "y": 0.3364565574968006,
                    "z": 0.941293125881171,
                    "w": -0.01916428848098855,
                },
                "translation": {
                    "x": 90.45847018871761,
                    "y": 230.70152133008904,
                    "z": 41.49263715272844,
                },
                "scale3D": {
                    "x": 0.999999523162856,
                    "y": 1.000000238418533,
                    "z": 0.9999999999998401,
                },
            },
        },
        {
            "BoneName": "LeftToeBase",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.009353737532411505,
                    "y": -0.008827655672555945,
                    "z": -0.9998926355033925,
                    "w": 0.007021221801171861,
                },
                "translation": {
                    "x": 90.08738190796743,
                    "y": 243.35214205075667,
                    "z": 31.112123653956065,
                },
                "scale3D": {
                    "x": 1.000000357627485,
                    "y": 0.9999995827672841,
                    "z": 0.9999999999998401,
                },
            },
        },
        {
            "BoneName": "RightUpLeg",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.023161864789714864,
                    "y": 0.7041985091449395,
                    "z": 0.7092417106513309,
                    "w": -0.023327741249076165,
                },
                "translation": {
                    "x": 73.37982606887817,
                    "y": 229.03157862334965,
                    "z": 123.80844542694109,
                },
                "scale3D": {
                    "x": 0.9999997019767761,
                    "y": 1.0000001788139201,
                    "z": 0.9999994635582254,
                },
            },
        },
        {
            "BoneName": "RightLeg",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": -0.008301098884433722,
                    "y": -0.7042070495517992,
                    "z": -0.7098970007287277,
                    "w": 0.008352932132933805,
                },
                "translation": {
                    "x": 70.63083613374569,
                    "y": 229.78519806271467,
                    "z": 87.73165567433898,
                },
                "scale3D": {
                    "x": 0.9999996423721491,
                    "y": 1.0000001788139201,
                    "z": 0.999999582767451,
                },
            },
        },
        {
            "BoneName": "RightFoot",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.018883032543243815,
                    "y": 0.32524577067950305,
                    "z": 0.9452669723419637,
                    "w": 0.018137547751201084,
                },
                "translation": {
                    "x": 69.54152377985251,
                    "y": 230.15732025760022,
                    "z": 41.49262824362777,
                },
                "scale3D": {
                    "x": 0.999999880790643,
                    "y": 1.0000007748604745,
                    "z": 0.9999998211859307,
                },
            },
        },
        {
            "BoneName": "RightToeBase",
            "BoneSpace": SPACE,
            "ReturnValue": {
                "rotation": {
                    "x": 0.00893755516879865,
                    "y": -0.008814184764496026,
                    "z": -0.9998966263760661,
                    "w": -0.0070119053261841,
                },
                "translation": {
                    "x": 69.91262782927474,
                    "y": 243.44185895106156,
                    "z": 31.111957811619405,
                },
                "scale3D": {
                    "x": 0.999999880790643,
                    "y": 1.0000006556510925,
                    "z": 0.9999993443488577,
                },
            },
        },
    ]
    default_pose = {}
    for item in default_pose_dic:
        default_pose[item["BoneName"]] = {
            "translation": item["ReturnValue"]["translation"],
            "rotation": item["ReturnValue"]["rotation"],
        }

    spear_instance.engine_service.begin_tick()

    for bone_name in skeleton_mapping:
        translation = default_pose[bone_name]["translation"]
        rotation = default_pose[bone_name]["rotation"]

        args = {"BoneName": bone_name, "BoneSpace": SPACE}
        return_values = spear_instance.unreal_service.call_function(
            uobject=poseable_mesh_component,
            ufunction=get_bone_transform_by_name_func,
            args=args,
        )

        # args = {"BoneName": bone_name, "InTransform": return_values["ReturnValue"], "BoneSpace": SPACE}
        args = {
            "BoneName": bone_name,
            "InTransform": return_values["ReturnValue"],
            "BoneSpace": SPACE,
        }
        args["InTransform"]["translation"]["x"] = translation["x"]
        args["InTransform"]["translation"]["y"] = translation["y"]
        args["InTransform"]["translation"]["z"] = translation["z"]
        args["InTransform"]["rotation"]["w"] = rotation["w"]
        args["InTransform"]["rotation"]["x"] = rotation["x"]
        args["InTransform"]["rotation"]["y"] = rotation["y"]
        args["InTransform"]["rotation"]["z"] = rotation["z"]
        spear_instance.unreal_service.call_function(
            uobject=poseable_mesh_component,
            ufunction=set_bone_transform_by_name_func,
            args=args,
        )

    spear_instance.engine_service.tick()
    spear_instance.engine_service.end_tick()

    quit = False
    while not quit:

        # file_path = "/Users/liupan/repos/T2M-Blender/a person makes a big jump forward, then a big jump to the right, and then hops on one foot.json"
        file_path = (
            "/Users/liupan/repos/spear/examples/articulated_character/test_data.json"
        )

        # Load the animation data from the file
        with open(file_path, "r") as f:
            animation_data = json.load(f)

        keyframes = animation_data["keyframes_global"]

        for frame_str, bones_data in keyframes.items():
            frame = int(frame_str)
            if frame == 1:
                pos_offset = np.array(bones_data["pelvis"]["location"]) * 100
                pos_offset[1] = 0

            spear_instance.engine_service.begin_tick()

            for bone_name in skeleton_mapping:
                translation = (
                    np.array(bones_data[skeleton_mapping[bone_name]]["location"]) * 100
                    - pos_offset
                )
                rotation = bones_data[skeleton_mapping[bone_name]][
                    "rotation_quaternion"
                ]  # wxyz

                translation_default = default_pose[bone_name]["translation"]
                rotation_default = default_pose[bone_name]["rotation"]

                translation = [translation[0], translation[2], translation[1]]
                # # rotation = np.array([rotation[0], -rotation[1], -rotation[3], -rotation[2]])
                # rotation = np.array([rotation[0], -rotation[1], rotation[2], -rotation[3]])
                # rotation = np.array([rotation[0], -rotation[1], rotation[2], rotation[3]])

                rotation_xyzw = np.array(
                    [-rotation[1], rotation[2], -rotation[3], rotation[0]]
                )
                # q_rot = R.from_euler('x', -90, degrees=True).as_quat()
                q_rot = R.from_quat(
                    np.array(
                        [
                            rotation_default["x"],
                            rotation_default["y"],
                            rotation_default["z"],
                            rotation_default["w"],
                        ]
                    )
                ).as_quat()
                # Perform the rotation
                r = R.from_quat(rotation_xyzw)
                r_rotated = R.from_quat(q_rot) * r
                # Get the rotated quaternion
                rotation_xyzw = r_rotated.as_quat()
                rotation = np.array(
                    [
                        rotation_xyzw[3],
                        rotation_xyzw[0],
                        rotation_xyzw[1],
                        rotation_xyzw[2],
                    ]
                )

                # q_rot = R.from_euler('z', -90, degrees=True).as_quat()
                # r = R.from_quat(rotation)
                # r_rotated = R.from_quat(q_rot) * r
                # rotation = r_rotated.as_quat()
                # # rotation = np.array([rotation[0], -rotation[1], rotation[2], -rotation[3]])

                args = {"BoneName": bone_name, "BoneSpace": SPACE}
                # args = {"BoneName": bone_name, "BoneSpace": SPACE}
                return_values = spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=get_bone_transform_by_name_func,
                    args=args,
                )

                args = {
                    "BoneName": bone_name,
                    "InTransform": return_values["ReturnValue"],
                    "BoneSpace": SPACE,
                }
                # args = {"BoneName": bone_name, "InTransform": return_values["ReturnValue"], "BoneSpace": SPACE}
                args["InTransform"]["translation"]["x"] = translation[0]
                args["InTransform"]["translation"]["y"] = translation[1]
                args["InTransform"]["translation"]["z"] = translation[2]
                # args["InTransform"]["rotation"]["w"] = rotation[0]
                # args["InTransform"]["rotation"]["x"] = rotation[1]
                # args["InTransform"]["rotation"]["y"] = rotation[2]
                # args["InTransform"]["rotation"]["z"] = rotation[3]
                spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=set_bone_transform_by_name_func,
                    args=args,
                )

            spear_instance.engine_service.tick()
            spear_instance.engine_service.end_tick()

        key = readchar.readkey()
        spear.log("Received key: ", key)

        if key == "0":

            spear.log("Getting pose data for bones: ", bone_names)

            spear_instance.engine_service.begin_tick()

            for bone_name in bone_names:
                args = {"BoneName": bone_name, "BoneSpace": SPACE}
                return_values = spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=get_bone_transform_by_name_func,
                    args=args,
                )
                spear.log(return_values)

            spear_instance.engine_service.tick()
            spear_instance.engine_service.end_tick()

        elif key == "8":

            spear.log("Decreasing scale of bones: ", bone_names)

            spear_instance.engine_service.begin_tick()

            for bone_name in bone_names:
                args = {"BoneName": bone_name, "BoneSpace": SPACE}
                return_values = spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=get_bone_transform_by_name_func,
                    args=args,
                )

                args = {
                    "BoneName": bone_name,
                    "InTransform": return_values["ReturnValue"],
                    "BoneSpace": SPACE,
                }
                args["InTransform"]["scale3D"]["x"] = (
                    0.9 * args["InTransform"]["scale3D"]["x"]
                )
                args["InTransform"]["scale3D"]["y"] = (
                    0.9 * args["InTransform"]["scale3D"]["y"]
                )
                args["InTransform"]["scale3D"]["z"] = (
                    0.9 * args["InTransform"]["scale3D"]["z"]
                )
                spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=set_bone_transform_by_name_func,
                    args=args,
                )

            spear_instance.engine_service.tick()
            spear_instance.engine_service.end_tick()

        elif key == "9":

            spear.log("Increasing scale of bones: ", bone_names)

            spear_instance.engine_service.begin_tick()

            for bone_name in bone_names:
                args = {"BoneName": bone_name, "BoneSpace": SPACE}
                return_values = spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=get_bone_transform_by_name_func,
                    args=args,
                )

                args = {
                    "BoneName": bone_name,
                    "InTransform": return_values["ReturnValue"],
                    "BoneSpace": SPACE,
                }
                args["InTransform"]["scale3D"]["x"] = (
                    1.1 * args["InTransform"]["scale3D"]["x"]
                )
                args["InTransform"]["scale3D"]["y"] = (
                    1.1 * args["InTransform"]["scale3D"]["y"]
                )
                args["InTransform"]["scale3D"]["z"] = (
                    1.1 * args["InTransform"]["scale3D"]["z"]
                )
                spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=set_bone_transform_by_name_func,
                    args=args,
                )

            spear_instance.engine_service.tick()
            spear_instance.engine_service.end_tick()

        elif key == "1":

            spear.log("Increasing x: ", bone_names)

            spear_instance.engine_service.begin_tick()

            for bone_name in bone_names:
                args = {"BoneName": bone_name, "BoneSpace": SPACE}
                return_values = spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=get_bone_transform_by_name_func,
                    args=args,
                )

                args = {
                    "BoneName": bone_name,
                    "InTransform": return_values["ReturnValue"],
                    "BoneSpace": SPACE,
                }
                args["InTransform"]["translation"]["x"] = (
                    args["InTransform"]["translation"]["x"] + 100.0
                )
                spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=set_bone_transform_by_name_func,
                    args=args,
                )

            spear_instance.engine_service.tick()
            spear_instance.engine_service.end_tick()

        elif key == "2":

            spear.log("Increasing y: ", bone_names)

            spear_instance.engine_service.begin_tick()

            for bone_name in bone_names:
                args = {"BoneName": bone_name, "BoneSpace": SPACE}
                return_values = spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=get_bone_transform_by_name_func,
                    args=args,
                )

                args = {
                    "BoneName": bone_name,
                    "InTransform": return_values["ReturnValue"],
                    "BoneSpace": SPACE,
                }
                args["InTransform"]["translation"]["y"] = (
                    args["InTransform"]["translation"]["y"] + 100.0
                )
                spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=set_bone_transform_by_name_func,
                    args=args,
                )

            spear_instance.engine_service.tick()
            spear_instance.engine_service.end_tick()

        elif key == "3":

            spear.log("Increasing z: ", bone_names)

            spear_instance.engine_service.begin_tick()

            for bone_name in bone_names:
                args = {"BoneName": bone_name, "BoneSpace": SPACE}
                return_values = spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=get_bone_transform_by_name_func,
                    args=args,
                )

                args = {
                    "BoneName": bone_name,
                    "InTransform": return_values["ReturnValue"],
                    "BoneSpace": SPACE,
                }
                args["InTransform"]["translation"]["z"] = (
                    args["InTransform"]["translation"]["z"] + 100.0
                )
                spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=set_bone_transform_by_name_func,
                    args=args,
                )

            spear_instance.engine_service.tick()
            spear_instance.engine_service.end_tick()

        elif key == readchar.key.ESC:
            quit = True

    spear_instance.close()

    spear.log("Done.")
