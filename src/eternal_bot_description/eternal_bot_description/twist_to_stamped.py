import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped


class TwistToStamped(Node):
    """Relay /cmd_vel (Twist) to /diff_drive_controller/cmd_vel (TwistStamped)."""

    def __init__(self):
        super().__init__('twist_to_stamped')
        self.frame_id = self.declare_parameter('frame_id', 'base_link').value
        self.pub = self.create_publisher(TwistStamped, '/diff_drive_controller/cmd_vel', 10)
        self.create_subscription(Twist, '/cmd_vel', self.on_twist, 10)

    def on_twist(self, msg):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self.frame_id
        out.twist = msg
        self.pub.publish(out)


def main():
    rclpy.init()
    node = TwistToStamped()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
