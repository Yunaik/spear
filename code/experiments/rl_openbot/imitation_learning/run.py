#############################################################################

# Quick and dirty script to issue random commands to an OpenBot agent and get
# egocentric visual obsevations.

#############################################################################

# Before running this file, rename user_config.yaml.example -> user_config.yaml and modify it with appropriate paths for your system.
#
#
# python run.py -i 10 -r 3 -s "Data" -m "235114801" "235114775"
# python run.py -i 10 -r 3 -s "Infer" -m "235114801" "235114775"
# python run.py -i 10 -r 3 -s "Debug" -m "235114801" "235114775"

import argparse
import csv
import cv2
import datetime;
import math
from math import cos, sin, atan2, pi, isclose
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
import random
import shutil
#import tensorflow as tf
import tflite_runtime.interpreter as tflite
import time

from interiorsim import Env
from interiorsim.config import get_config
from interiorsim.constants import INTERIORSIM_ROOT_DIR



def Clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

def iterationAutopilot(desiredPositionXY, actualPoseYawXY, linVelNorm, yawVel, Kp_lin, Kd_lin, Kp_ang, Kd_ang, acceptanceRadius, forwardMinAngle, controlSaturation):

    targetLocationReached = False
    forwardCtrl = 0.0
    rightCtrl = 0.0
    action = np.array([0.0,0.0])
    deltaYaw = 0.0
    forward = np.array([1,0]) # Front axis is the X axis.
    forwardRotated = np.array([0,0])

    # Target error vector (global coordinate system):
    relativePositionToTarget = desiredPositionXY - np.array([actualPoseYawXY[1],actualPoseYawXY[2]])
        
    # Compute Euclidean distance to target in [m]:
    dist = np.linalg.norm(relativePositionToTarget)*0.01

    # If the waypoint is reached, send zero command:
    if dist < acceptanceRadius :

        targetLocationReached = True;
        print("Target reached !")

    # Otherwise compute the PID command:
    else:
    
        # Compute robot forward axis (global coordinate system):
        yawVehicle = actualPoseYawXY[0];
        rot = np.array([[cos(yawVehicle), -sin(yawVehicle)], [sin(yawVehicle), cos(yawVehicle)]])

        forwardRotated = np.dot(rot, forward)

        # Compute yaw:
        deltaYaw = atan2(forwardRotated[1], forwardRotated[0]) - atan2(relativePositionToTarget[1], relativePositionToTarget[0])

        # Fit to range [-pi, pi]:
        if deltaYaw > math.pi:
            deltaYaw -= 2 * math.pi
        elif deltaYaw <= -math.pi:
            deltaYaw += 2 * math.pi

        linVel = linVelNorm * 0.036; # In [m/s]

        rightCtrl = -Kp_ang * deltaYaw - Kd_ang * yawVel;
        Clamp(rightCtrl, -controlSaturation, controlSaturation)

        if abs(deltaYaw) < forwardMinAngle :
            forwardCtrl = Kp_lin * dist - Kd_lin * linVel
            forwardCtrl = Clamp(forwardCtrl, -controlSaturation, controlSaturation)
            forwardCtrl *= abs(cos(deltaYaw)); # Full throttle if the vehicle facing the objective. Otherwise give more priority to the yaw command.

        # Compute action:
        leftWheelCommand = forwardCtrl + rightCtrl
        leftWheelCommand = Clamp(leftWheelCommand, -controlSaturation, controlSaturation)
        
        rightWheelCommand = forwardCtrl - rightCtrl
        rightWheelCommand = Clamp(rightWheelCommand, -controlSaturation, controlSaturation)
        
        action = np.array([leftWheelCommand,rightWheelCommand])

    print(f"dist: {dist} m")
    print(f"deltaYaw: {deltaYaw}")
    print(f"rightCtrl: {rightCtrl}")
    print(f"forwardCtrl: {forwardCtrl}")
    print(f"action: {action[0]}, {action[1]}")

    return action, targetLocationReached
    
    

if __name__ == "__main__":

    # List of config files to be used
    config_files = []

    # Add default config files first and then user config files
    config_files.append(os.path.join(os.getcwd(), "user_config.yaml"))

    # Load configs
    config = get_config(config_files)
    print(config)

    # Parse input script arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--iterations", type=int, help="number of iterations through the environment", required=True)
    parser.add_argument("-r", "--runs", type=int, help="number of distinct runs in the considered environment", required=True)
    parser.add_argument("-s", "--setup", type=str, help="Data (for data collection), Infer (for ANN inference), Debug (for debug purposes only)", required=True)
    parser.add_argument("-m", "--map", nargs="+", default=[""], help="Array of map references. A number of s distinct runs will be executed in each map. This argument overwrites the MAP_ID argument and allows collecting data in multiple environments programatically", required=False)
    args = parser.parse_args()

    if args.map == [""]: # Use the default MAP_ID argument from parameter file
        if config.INTERIORSIM.MAP_ID == "":
            mapNames = ["simpleMap"]
        elif config.INTERIORSIM.MAP_ID[0:15] == "/Game/Maps/Map_":
            mapNames = [config.INTERIORSIM.MAP_ID[15:]]
        else:
            mapNames = ["errorMap"]
    else: # Overwrite the map value
        mapNames = args.map

    numIter = args.iterations
    learningMode = args.setup
    runs = args.runs

    if learningMode == "Data":

        # Main loop, executing a set of random actions, getting observations and storing everything in a set of files:

        # The agent makes the following observations:

        # ---> left wheel commands in the range [-1, 1]
        # ---> right wheel commands in the range [-1, 1]
        # ---> X position in world frame.
        # ---> Y position in world frame.
        # ---> Z position in world frame.
        # ---> Roll in world frame.
        # ---> Pitch in world frame.
        # ---> Yaw in world frame.
        # ---> X position of the next waypoint in world frame.
        # ---> Y position of the next waypoint in world frame.

        config.defrost()
        config.SIMULATION_CONTROLLER.OPENBOT_AGENT_CONTROLLER.PHYSICAL_OBSERVATION_MODE = "full-pose"
        config.freeze()

        speedMultiplier = 1

        for mapName in mapNames: # For each map

            # Load the correct map:
            config.defrost()
            config.INTERIORSIM.MAP_ID = "/Game/Maps/Map_" + mapName
            config.freeze()

            # Create Env object:
            env = Env(config)

            run = 0
            while run < runs:

                collisionFlag = False
                goalReachedFlag = False
                array_obs = np.empty([numIter, 11])
                executedIterations = 0

                folderName = f"dataset/uploaded/run_{mapName}_{run}"
                dataFolderName = folderName+"/data/"
                os.makedirs(dataFolderName, exist_ok=True)
                os.makedirs(dataFolderName+"sensor_data", exist_ok=True)
                os.makedirs(dataFolderName+"images", exist_ok=True)

                print("----------------------")
                print(f"run {run} over {runs}")
                print("----------------------")

                # Reset the simulation to get the first observation
                obs = env.reset()
                actualPoseYawXY = np.array([obs["physical_observation"][7], obs["physical_observation"][2], obs["physical_observation"][3]]) # [Yaw, X, Y], for velocity initialization
                desiredPositionXY = np.array([obs["physical_observation"][8], obs["physical_observation"][9]]) # [Xdes, Ydes]

                # Take a few steps:
                for i in range(numIter):

                    print(f"iteration {i} over {numIter}")

                    executedIterations = i+1
                    ct = datetime.datetime.now()
                    ts = 10000*ct.timestamp()

                    # Run autopilot:
                    Kp_lin = config.ROBOT_SIM.PROPORTIONAL_GAIN_DIST
                    Kd_lin = config.ROBOT_SIM.DERIVATIVE_GAIN_DIST
                    Kp_ang = config.ROBOT_SIM.PROPORTIONAL_GAIN_HEADING
                    Kd_ang = config.ROBOT_SIM.DERIVATIVE_GAIN_HEADING
                    acceptanceRadius = config.ROBOT_SIM.ACCEPTANCE_RADIUS
                    forwardMinAngle = config.ROBOT_SIM.FORWARD_MIN_ANGLE
                    controlSaturation = config.ROBOT_SIM.CONTROL_SATURATION
                    dt = 0.1

                    # XY position of the next waypoint in world frame:
                    dXY = np.array([obs["physical_observation"][2], obs["physical_observation"][3]]) - desiredPositionXY
                    desiredPositionXY = np.array([obs["physical_observation"][8], obs["physical_observation"][9]]) # [Xdes, Ydes]

                    # Current position and heading of the vehicle in world frame:
                    dYaw = obs["physical_observation"][7] - actualPoseYawXY[0]
                    actualPoseYawXY = np.array([obs["physical_observation"][7], obs["physical_observation"][2], obs["physical_observation"][3]]) # [Yaw, X, Y]

                    # Numerical diff:
                    linVelNorm = np.linalg.norm(dXY/dt)
                    yawVel = dYaw/dt

                    action, targetLocationReached = iterationAutopilot(desiredPositionXY, actualPoseYawXY, linVelNorm, yawVel, Kp_lin, Kd_lin, Kp_ang, Kd_ang, acceptanceRadius, forwardMinAngle, controlSaturation)

                    # Send action to the agent and collect observations:
                    obs, reward, done, info = env.step({"apply_voltage": [action[0], action[1]]})

                    # Fill an array with the different observations:
                    array_obs[i][0] = speedMultiplier*obs["physical_observation"][0] # ctrl left
                    array_obs[i][1] = speedMultiplier*obs["physical_observation"][1] # ctrl right
                    array_obs[i][2] = obs["physical_observation"][2] # agent pos X wrt. world
                    array_obs[i][3] = obs["physical_observation"][3] # agent pos Y wrt. world
                    array_obs[i][4] = obs["physical_observation"][4] # agent pos Z wrt. world
                    array_obs[i][5] = obs["physical_observation"][5] # agent Roll wrt. world
                    array_obs[i][6] = obs["physical_observation"][6] # agent Pitch wrt. world
                    array_obs[i][7] = obs["physical_observation"][7] # agent Yaw wrt. world
                    array_obs[i][8] = obs["physical_observation"][8] # desired (waypoint) agent pos X wrt. world
                    array_obs[i][9] = obs["physical_observation"][9] # desired (waypoint) agent pos Y wrt. world
                    array_obs[i][10] = ts # time stamp
                    
                    
                    print(f"Action: {array_obs[i][0]}, {array_obs[i][1]}")
                    print(f"Pose: {array_obs[i][2], array_obs[i][3], array_obs[i][4], array_obs[i][5], array_obs[i][6], array_obs[i][7]}")

                    # Save the images:
                    im = Image.fromarray(obs["visual_observation"])
                    im.save(dataFolderName+"images/%d.jpeg" % i)

                    # Interrupt the step loop if the done flag is raised:
                    if done:
                        if info["hit_obstacle"]:
                            print("Collision detected ! Killing simulation and restarting run...")
                            collisionFlag = True

                        if info["hit_goal"]:
                            print("Goal reached !")
                            goalReachedFlag = True

                        break

                if collisionFlag == True:
                    print("Restarting run...")
                    shutil.rmtree(folderName)

                else:
                    run = run + 1

                    print("Filling database...")
                    f_ctrl = open(dataFolderName+"sensor_data/ctrlLog.txt", 'w') # Low-level commands sent to the motors
                    f_goal = open(dataFolderName+"sensor_data/goalLog.txt", 'w') # High level commands
                    f_rgb = open(dataFolderName+"sensor_data/rgbFrames.txt", 'w') # Reference of the images correespoinding to each control input
                    f_pose = open(dataFolderName+"sensor_data/poseData.txt", 'w') # Raw pose data (for debug purposes and (also) to prevent one from having to re-run the data collection in case of a deg2rad issue...)

                    writer_ctrl = csv.writer(f_ctrl, delimiter=",")
                    writer_ctrl.writerow( ('timestamp[ns]','leftCtrl','rightCtrl') )
                    writer_pose = csv.writer(f_pose , delimiter=",")
                    writer_pose.writerow( ('timestamp[ns]','posX','posY','posZ','rollAngle','pitchAngle','yawAngle') )
                    writer_goal = csv.writer(f_goal, delimiter=",")
                    writer_goal.writerow( ('timestamp[ns]','dist','sinYaw','cosYaw') )
                    writer_rgb = csv.writer(f_rgb, delimiter=",")
                    writer_rgb.writerow( ('timestamp[ns]','frame') )

                    goalLocation = np.array([array_obs[numIter-1][2],array_obs[numIter-1][3]]) # use the vehicle last location as goal
                    forward = np.array([1,0]) # Front axis is the X axis.
                    forwardRotated = np.array([0,0])

                    for i in range(executedIterations):

                        # Target error vector (global coordinate system):
                        relativePositionToTarget = goalLocation - np.array([array_obs[i][2],array_obs[i][3]])

                        # Compute Euclidean distance to target:
                        dist = np.linalg.norm(relativePositionToTarget)

                        # Compute robot forward axis (global coordinate system):
                        yawVehicle = array_obs[i][7];
                        rot = np.array([[cos(yawVehicle), -sin(yawVehicle)], [sin(yawVehicle), cos(yawVehicle)]])

                        forwardRotated = np.dot(rot, forward)

                        # Compute yaw:
                        deltaYaw = atan2(forwardRotated[1], forwardRotated[0]) - atan2(relativePositionToTarget[1], relativePositionToTarget[0])

                        # Fit to range [-pi, pi]:
                        if deltaYaw > math.pi:
                            deltaYaw -= 2 * math.pi
                        elif deltaYaw <= -math.pi:
                            deltaYaw += 2 * math.pi

                        # Check the actual OpenBot code:
                        # https://github.com/isl-org/OpenBot/blob/7868c54742f8ba3df0ba2a886247a753df982772/android/app/src/main/java/org/openbot/pointGoalNavigation/PointGoalNavigationFragment.java#L103
                        sinYaw = sin(deltaYaw);
                        cosYaw = cos(deltaYaw);

                        # Write pose data
                        writer_pose.writerow( (int(array_obs[i][8]), array_obs[i][2], array_obs[i][3], array_obs[i][4], array_obs[i][5], array_obs[i][6], array_obs[i][7]) )

                        # Write the low-level control observation into a file:
                        writer_ctrl.writerow( (int(array_obs[i][8]), array_obs[i][0], array_obs[i][1]) )

                        # Write the corresponding image index into a file:
                        writer_rgb.writerow( (int(array_obs[i][8]), i) )

                        # Write the corresponding high level command into a file:
                        # For imitation learning, use the latest position as a goal
                        writer_goal.writerow( (int(array_obs[i][8]), dist/100, sinYaw, cosYaw) )

                    f_ctrl.close()
                    f_pose.close()
                    f_goal.close()
                    f_rgb.close()

                # Reset the environment after each run:
                env.reset()

        # Close the environment:
        env.close()
        time.sleep(3)

    elif learningMode == "Infer":

        # Main loop, testing a trained neural policy:

        # The agent makes the following observations:

        # ---> left wheel commands in the range [-1, 1]
        # ---> right wheel commands in the range [-1, 1]
        # ---> Euclidean distance between current x-y position and target x-y position.
        # ---> Sinus of the relative yaw between current pose and target pose.
        # ---> Cosinus of the relative yaw between current pose and target pose.

        config.defrost()
        config.SIMULATION_CONTROLLER.OPENBOT_AGENT_CONTROLLER.PHYSICAL_OBSERVATION_MODE = "dist-sin-cos" # Owerwrite observation mode to prevent crash.
        config.freeze()

        # Load TFLite model and allocate tensors.
        interpreter = tflite.Interpreter("./models/TestSession_1_pilot_net_lr0.0001_bz64_bn/checkpoints/best-val.tflite")
        interpreter.allocate_tensors()

        # Get input and output tensors.
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        print(input_details)
        print(output_details)

        img_input = np.array(np.random.random_sample(input_details[0]["shape"]), dtype=np.float32)
        cmd_input = np.array(np.random.random_sample(input_details[1]["shape"]), dtype=np.float32)

        for mapName in mapNames: # For each map

            # Load the correct map:
            config.defrost()
            config.INTERIORSIM.MAP_ID = "/Game/Maps/Map_" + mapName
            config.freeze()

            # Create Env object:
            env = Env(config)

            run = 0
            while run < runs:

                collisionFlag = False
                goalReachedFlag = False
                result = np.empty((0, 2), dtype=float)
                executedIterations = 0

                print("----------------------")
                print(f"run {run} over {runs}")
                print("----------------------")

                # Reset the simulation to get the first observation
                obs = env.reset()

                # Take a few steps:
                for i in range(numIter):

                    print(f"iteration {i} over {numIter}")

                    # Process (crop) visual observations:
                    img_input = np.float32(obs["visual_observation"])/255
                    ##img_input = tf.image.crop_to_bounding_box(img_input, tf.shape(img_input)[0] - 90, tf.shape(img_input)[1] - 160, 90, 160)

                    # Physical observations
                    cmd_input[0][0] = np.float32(obs["physical_observation"][2])/100
                    cmd_input[0][1] = np.float32(obs["physical_observation"][3])
                    cmd_input[0][2] = np.float32(obs["physical_observation"][4])

                    # Inference:
                    interpreter.set_tensor(input_details[0]["index"], np.expand_dims(img_input, axis=0))
                    interpreter.set_tensor(input_details[1]["index"], cmd_input)
                    start_time = time.time()
                    interpreter.invoke()
                    stop_time = time.time()
                    print('Infererence time: {:.3f}ms'.format((stop_time - start_time) * 1000))

                    # Output of the Artificial Neural Network
                    output = interpreter.get_tensor(output_details[0]["index"])

                    # Command
                    action = np.clip(np.concatenate((result, output.astype(float))), -1.0, 1.0)
                    print(action)

                    # Send action to the agent:
                    obs, reward, done, info = env.step({"apply_voltage": action})

                    # Interrupt the step loop if the done flag is raised:
                    if done:
                        if info["hit_obstacle"]:
                            print("Collision detected ! Killing simulation and restarting run...")
                            collisionFlag = True

                        if info["hit_goal"]:
                            print("Goal reached !")
                            goalReachedFlag = True

                        break

                # If the run was executed with a collision event, re-execute it:
                if collisionFlag == True:
                    print("Restarting run...")

                # Otherwise move to the next run:
                else:
                    run = run + 1

        # Close the environment:
        env.close()

    elif learningMode == "Debug": # Just play with the keyboard while checking the observations

        # Load the correct map and observation mode:
        config.defrost()
        config.INTERIORSIM.MAP_ID = "/Game/Maps/Map_" + mapNames[0]
        config.SIMULATION_CONTROLLER.OPENBOT_AGENT_CONTROLLER.PHYSICAL_OBSERVATION_MODE = "full-pose"
        config.freeze()

        # Create Env object:
        env = Env(config)

        # Reset the simulation to get the first observation
        obs = env.reset()
        actualPoseYawXY = np.array([obs["physical_observation"][7], obs["physical_observation"][2], obs["physical_observation"][3]]) # [Yaw, X, Y], for velocity initialization
        desiredPositionXY = np.array([obs["physical_observation"][2], obs["physical_observation"][3]]) # [X, Y]

        print(obs["visual_observation"].shape, obs["visual_observation"].dtype)

        cv2.imshow("visual_observation", obs["visual_observation"][:,:,[2,1,0]]) # OpenCV expects BGR instead of RGB
        cv2.waitKey(0)

        # Take a few steps:
        for i in range(numIter):

            print(f"iteration {i} over {numIter}")

            executedIterations = i+1
            ct = datetime.datetime.now()
            ts = 10000*ct.timestamp()

            # Run autopilot:
            Kp_lin = config.ROBOT_SIM.PROPORTIONAL_GAIN_DIST
            Kd_lin = config.ROBOT_SIM.DERIVATIVE_GAIN_DIST
            Kp_ang = config.ROBOT_SIM.PROPORTIONAL_GAIN_HEADING
            Kd_ang = config.ROBOT_SIM.DERIVATIVE_GAIN_HEADING
            acceptanceRadius = config.ROBOT_SIM.ACCEPTANCE_RADIUS
            forwardMinAngle = config.ROBOT_SIM.FORWARD_MIN_ANGLE
            controlSaturation = config.ROBOT_SIM.CONTROL_SATURATION
            dt = 0.1

            # XY position of the next waypoint in world frame:
            dXY = np.array([obs["physical_observation"][7], obs["physical_observation"][2], obs["physical_observation"][3]]) - desiredPositionXY
            desiredPositionXY = np.array([obs["physical_observation"][8], obs["physical_observation"][9]]) # [Xdes, Ydes]

            # Current position and heading of the vehicle in world frame:
            dYaw = obs["physical_observation"][7] - actualPoseYawXY[0]
            actualPoseYawXY = np.array([obs["physical_observation"][7], obs["physical_observation"][2], obs["physical_observation"][3]]) # [Yaw, X, Y]

            # Numerical diff:
            linVelNorm = np.linalg.norm(dXY/dt)
            yawVel = dYaw/dt

            action, targetLocationReached = iterationAutopilot(desiredPositionXY, actualPoseYawXY, linVelNorm, yawVel, Kp_lin, Kd_lin, Kp_ang, Kd_ang, acceptanceRadius, forwardMinAngle, controlSaturation)

            # Send action to the agent and collect observations:

            obs, reward, done, info = env.step({"apply_voltage": action})
            print(obs["visual_observation"].shape, obs["visual_observation"].dtype, reward, done, info)

            cv2.imshow("visual_observation", obs["visual_observation"][:,:,[2,1,0]]) # OpenCV expects BGR instead of RGB
            cv2.waitKey(0)

            #if done:
            #    print("Reset run...")
            #    env.reset()

        cv2.destroyAllWindows()

        # Close the environment:
        env.close()

    else:

        print("No mode selected...")

