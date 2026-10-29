from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from nav2_common.launch import RewrittenYaml
from os.path import join

# Runs on the Raspberry Pi. Start gazebo.launch.py on the laptop first (same ROS_DOMAIN_ID).
# slam_toolbox in localization mode on maps/obs_map2_serial, then Nav2 once map->odom exists (nav.launch.py).
# The yaml's map_file_name is an absolute path from one dev machine (/home/parallels/...), so it is
# rewritten to the installed map. RViz and teleop stay on the laptop.
def generate_launch_description():
    pkg = get_package_share_directory('eternal_bot_description')
    slam_toolbox = get_package_share_directory('slam_toolbox')

    slam_params = RewrittenYaml(
        source_file=join(pkg, 'config', 'mapper_params_online_async.yaml'),
        param_rewrites={'map_file_name': join(pkg, 'maps', 'obs_map2_serial')},
        convert_types=True,
    )

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(join(slam_toolbox, 'launch', 'online_async_launch.py')),
            launch_arguments={
                'slam_params_file': slam_params,
                'use_sim_time': 'true',
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(join(pkg, 'launch', 'nav.launch.py')),
        ),
    ])
