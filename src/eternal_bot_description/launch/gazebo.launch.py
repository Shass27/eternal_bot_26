import os
import re
import shutil
import subprocess
import tempfile
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
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

   
    # world:=arena (default) | arena_obs | empty ; worlds live in share/<pkg>/worlds
    world_arg = DeclareLaunchArgument(
        'world', default_value='arena',
        description='World to load: arena, arena_obs or empty (Gazebo empty.sdf)')
    world = LaunchConfiguration('world')
    worlds_dir = join(pkg_ros_gz_rbot, 'worlds')
    world_file = PythonExpression([
        "'empty.sdf' if '", world, "' == 'empty' else '", worlds_dir, "/' + '", world, "' + '.world'"
    ])

    # render_engine:=ogre2 (default) | ogre ; use ogre in a VM. Applies to the gz GUI/server and the lidar Sensors plugin
    render_engine_arg = DeclareLaunchArgument(
        'render_engine', default_value='ogre2',
        description='Gazebo render engine: ogre2 (native GPU) or ogre (VM)')
    render_engine = LaunchConfiguration('render_engine')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")),
        launch_arguments={"gz_args": ["-r -v 4 --render-engine ", render_engine, " ", world_file]}.items()
    )

    # URDF cannot express fdir1's frame; convert to SDF and pin it to base_link so roller-friction directions don't rotate with the wheels
    with tempfile.NamedTemporaryFile('w', suffix='.urdf') as f:
        f.write(robot_description['robot_description']); f.flush()
        gz = shutil.which('gz') or '/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz'
        sdf = subprocess.run([gz, 'sdf', '-p', f.name], capture_output=True, text=True, check=True).stdout
    sdf = sdf.replace('<sdf version', '<sdf xmlns:gz="http://gazebosim.org/schema" version', 1)
    sdf = re.sub(r'<fdir1>', '<fdir1 gz:expressed_in="base_link">', sdf)
    # the Sensors plugin's <render_engine> is baked into the model; splice the launch argument in at spawn time
    sdf_parts = re.split(r'(?<=<render_engine>)[^<]*(?=</render_engine>)', sdf)
    sdf_arg = [sdf_parts[0]] + [x for part in sdf_parts[1:] for x in (render_engine, part)]

    spawn_robot_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            "-string", sdf_arg,
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

    # arbitrates cmd_vel_safe (Nav2) / key_vel_filtered (key_teleop) / cmd_vel_emergency (+ e_stop lock) into /cmd_vel
    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        parameters=[join(pkg_ros_gz_rbot, 'config', 'twist_mux.yaml'), {'use_sim_time': True}],
        remappings=[('cmd_vel_out', '/cmd_vel')],
        output='screen'
    )

    # drops all-zero key_teleop commands so an idle keyboard doesn't override nav
    key_filter = Node(
        package='eternal_bot_description',
        executable='nonzero_filter',
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    return LaunchDescription([
        world_arg,
        render_engine_arg,
        gazebo,
        spawn_robot,
        ros_gz_bridge,
        twist_mux,
        key_filter,
        robot_state_publisher,
    ])
