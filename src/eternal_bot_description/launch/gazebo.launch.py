import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
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
        parameters=[robot_description],
    )

   
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")),
        # launch_arguments={"gz_args": "-r -v 4 empty.sdf"}.items() use it in native installation of ubuntu
        launch_arguments={"gz_args": "-r -v 4 --render-engine ogre empty.sdf"}.items()
    )

    spawn_robot_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            "-topic", "/robot_description",
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

    # spawn controllers only after the robot spawn process has finished, plus a short delay
    def spawner(name):
        return Node(
            package='controller_manager',
            executable='spawner',
            arguments=[name, '--controller-manager', '/controller_manager'],
            output='screen',
        )

    joint_state_broadcaster = spawner('joint_state_broadcaster')
    diff_drive_controller = spawner('diff_drive_controller')

    spawn_jsb_after_robot = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot_node,
            on_exit=[TimerAction(period=3.0, actions=[joint_state_broadcaster])],
        )
    )
    spawn_ddc_after_jsb = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[diff_drive_controller],
        )
    )

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': ros_gz_bridge_config}],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        spawn_robot,
        spawn_jsb_after_robot,
        spawn_ddc_after_jsb,
        ros_gz_bridge,
        robot_state_publisher,
    ])
