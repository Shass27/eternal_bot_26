import os
import re
import shutil
import subprocess
import tempfile
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro
from os.path import join

def generate_launch_description():

    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_ros_gz_rbot = get_package_share_directory('eternal_bot_description')


    robot_description_file = os.path.join(pkg_ros_gz_rbot, 'urdf', 'eternal_bot.xacro')
    ros_gz_bridge_config = os.path.join(pkg_ros_gz_rbot, 'config', 'ros_gz_bridge_gazebo.yaml')
    
    robot_description_config = xacro.process_file(robot_description_file)
    robot_description = {'robot_description': robot_description_config.toxml()}

   
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': True}],
    )

   
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")),
        # launch_arguments={"gz_args": "-r -v 4 empty.sdf"}.items() use it in native installation of ubuntu
        launch_arguments={"gz_args": "-r -v 4 --render-engine ogre empty.sdf"}.items()
    )

    # URDF cannot express fdir1's frame; convert to SDF and pin it to base_link so roller-friction directions don't rotate with the wheels
    with tempfile.NamedTemporaryFile('w', suffix='.urdf') as f:
        f.write(robot_description['robot_description']); f.flush()
        gz = shutil.which('gz') or '/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz'
        sdf = subprocess.run([gz, 'sdf', '-p', f.name], capture_output=True, text=True, check=True).stdout
    sdf = sdf.replace('<sdf version', '<sdf xmlns:gz="http://gazebosim.org/schema" version', 1)
    sdf = re.sub(r'<fdir1>', '<fdir1 gz:expressed_in="base_link">', sdf)

    spawn_robot_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            "-string", sdf,
            "-name", "eternal_bot",
            "-allow_renaming", "false",  # prevents "_1" duplicate
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.32",
            "-Y", "0.0"
        ],
        output='screen'
    )
    spawn_robot = TimerAction(period=5.0, actions=[spawn_robot_node])

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': ros_gz_bridge_config}],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        spawn_robot,
        ros_gz_bridge,
        robot_state_publisher,
    ])
