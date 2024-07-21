#
# Copyright(c) 2022 Intel. Licensed under the MIT License <http://opensource.org/licenses/MIT>.
#

import os
import readchar
import spear
import json
import numpy as np
from scipy.spatial.transform import Rotation as R


def get_quat_from_blender_quat(blender_quat):
    return R.from_quat(
        [blender_quat[1], blender_quat[2], blender_quat[3], blender_quat[0]]
    )
    # blender quat is wxyz, scipy needs scalar last.
    # Verified by calling R.from_quat([0,0,0,1]).as_matrix() resulting in eye(3)


def get_quat_from_ue_quat(ue_quat):
    return R.from_quat(
        [ue_quat["x"], ue_quat["y"], ue_quat["z"], ue_quat["w"]]
    )  # R.from_quat expects xyzw


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

    bone_names = list(skeleton_mapping.keys())

    quit = False
    while not quit:

        file_path = "/Users/yuankai/code/github/spear/examples/articulated_character/test_data.json"

        # Load the animation data from the file
        with open(file_path, "r") as f:
            animation_data = json.load(f)

        keyframes = animation_data["keyframes_global"]
        # Getting UE orientation offsets
        spear_instance.engine_service.begin_tick()

        orientation_offset = {}
        for bone_name_ue in bone_names:
            args = {"BoneName": bone_name_ue, "BoneSpace": SPACE}
            return_values = spear_instance.unreal_service.call_function(
                uobject=poseable_mesh_component,
                ufunction=get_bone_transform_by_name_func,
                args=args,
            )
            orientation_offset[bone_name_ue] = get_quat_from_ue_quat(
                return_values["ReturnValue"]["rotation"]
            )
        spear_instance.engine_service.tick()
        spear_instance.engine_service.end_tick()

        for frame_str, bones_data in keyframes.items():
            frame = int(frame_str)
            if frame == 1:
                pos_offset = np.array(bones_data["pelvis"]["location"]) * 100
                pos_offset[1] = 0

            spear_instance.engine_service.begin_tick()
            # pelvis_z = bones_data["pelvis"]["location"][1] * 100
            # args = {"BoneName": "Hips", "BoneSpace": SPACE}
            # return_values = spear_instance.unreal_service.call_function(
            #     uobject=poseable_mesh_component,
            #     ufunction=get_bone_transform_by_name_func,
            #     args=args,
            # )
            # pelvis_ue_z = return_values["ReturnValue"]["translation"]["z"]
            for bone_name_ue, bone_name_ref_data in skeleton_mapping.items():
                # print(
                #     f'{bone_name_ue} z distance to pelvis: {bones_data[bone_name_ref_data]["location"][1]*100- pelvis_z :.2f} '
                # )
                # continue
                # if not (bone_name_ue == "Head"):
                #     continue
                translation = (
                    np.array(bones_data[bone_name_ref_data]["location"]) * 100
                    - pos_offset
                )
                desired_rotation_blender = bones_data[bone_name_ref_data][
                    "rotation_quaternion"
                ]  # wxyz
                desired_rotation = get_quat_from_blender_quat(desired_rotation_blender)
                rotation = desired_rotation.inv() * orientation_offset[bone_name_ue]
                translation = [
                    translation[0],
                    translation[2],
                    translation[1],
                ]  # UE is a left-handed system

                args = {"BoneName": bone_name_ue, "BoneSpace": SPACE}
                return_values = spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=get_bone_transform_by_name_func,
                    args=args,
                )

                args = {
                    "BoneName": bone_name_ue,
                    "InTransform": return_values["ReturnValue"],
                    "BoneSpace": SPACE,
                }

                # args["InTransform"]["translation"]["x"] = translation[0]
                # args["InTransform"]["translation"]["y"] = translation[1]
                # args["InTransform"]["translation"]["z"] = translation[2]

                args["InTransform"]["rotation"]["w"] = rotation.as_quat()[3]
                args["InTransform"]["rotation"]["x"] = rotation.as_quat()[0]
                args["InTransform"]["rotation"]["y"] = rotation.as_quat()[1]
                args["InTransform"]["rotation"]["z"] = rotation.as_quat()[2]

                spear_instance.unreal_service.call_function(
                    uobject=poseable_mesh_component,
                    ufunction=set_bone_transform_by_name_func,
                    args=args,
                )

                # args = {"BoneName": bone_name_ue, "BoneSpace": SPACE}
                # return_values = spear_instance.unreal_service.call_function(
                #     uobject=poseable_mesh_component,
                #     ufunction=get_bone_transform_by_name_func,
                #     args=args,
                # )
                # print(
                #     f'{bone_name_ue} z distance to pelvis for UE: {return_values["ReturnValue"]["translation"]["z"]- pelvis_ue_z :.2f} '
                # )
                # print(
                #     f'{bone_name_ue} difference in z: {translation[2] - return_values["ReturnValue"]["translation"]["z"]:.2f} with blender: {translation[2]:.2f} and ue: {return_values["ReturnValue"]["translation"]["z"]:.2f}'
                # )
            spear_instance.engine_service.tick()
            spear_instance.engine_service.end_tick()
            print("Tick finished")
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

        elif key == readchar.key.ESC:
            quit = True

    spear_instance.close()

    spear.log("Done.")
