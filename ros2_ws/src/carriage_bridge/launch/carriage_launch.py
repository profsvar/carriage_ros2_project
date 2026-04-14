from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory("carriage_bridge")
    urdf = os.path.join(pkg, "urdf", "carriage.urdf.xacro")
    return LaunchDescription([
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[{"robot_description": Command(["xacro ", urdf])}]),
        Node(package="carriage_bridge", executable="carriage_bridge_node.py",
             parameters=[{"port": "/dev/ttyAMA0", "baudrate": 115200,
                          "slave_addr": 202, "poll_rate": 10.0}]),
    ])
