from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from os.path import join

# Nav2 servers (no map_server/amcl: slam_toolbox in localization mode provides /map and map->odom).
# Start gazebo.launch.py and slam.launch.py first; Nav2 is held back until map->odom exists, because the
# lifecycle manager aborts the whole bringup if the global costmap can't find the map frame in time.
# Output chain:
#   controller -> cmd_vel_nav -> velocity_smoother -> cmd_vel_smoothed -> collision_monitor -> cmd_vel_safe -> twist_mux -> /cmd_vel
WAIT_FOR_MAP = '''
import rclpy
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
rclpy.init()
n = rclpy.create_node('wait_for_map_frame')
b = Buffer(); TransformListener(b, n)
n.get_logger().info('waiting for map->odom (start slam.launch.py)...')
while rclpy.ok() and not b.can_transform('map', 'odom', Time()):
    rclpy.spin_once(n, timeout_sec=0.2)
n.get_logger().info('map->odom found, starting Nav2')
'''


def generate_launch_description():
    pkg = get_package_share_directory('eternal_bot_description')
    nav2_bringup = get_package_share_directory('nav2_bringup')

    wait = ExecuteProcess(cmd=['python3', '-c', WAIT_FOR_MAP], output='screen')
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(join(nav2_bringup, 'launch', 'navigation_launch.py')),
        launch_arguments={
            'params_file': join(pkg, 'config', 'nav2_params.yaml'),
            'use_sim_time': 'true',
        }.items(),
    )

    return LaunchDescription([
        wait,
        RegisterEventHandler(OnProcessExit(target_action=wait, on_exit=[nav2])),
    ])
