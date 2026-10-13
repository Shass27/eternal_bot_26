from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from os.path import join

# slam_toolbox online-async on top of a running sim (gazebo.launch.py). Teleop needs its own terminal.
# This remap bypasses twist_mux on purpose (from-scratch mapping); drop it to drive through the mux:
#   ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false -r key_vel:=cmd_vel
def generate_launch_description():
    pkg = get_package_share_directory('eternal_bot_description')
    slam_toolbox = get_package_share_directory('slam_toolbox')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(join(slam_toolbox, 'launch', 'online_async_launch.py')),
            launch_arguments={
                'slam_params_file': join(pkg, 'config', 'mapper_params_online_async.yaml'),
                'use_sim_time': 'true',
            }.items(),
        ),
    ])
