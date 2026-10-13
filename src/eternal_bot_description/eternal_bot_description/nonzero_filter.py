import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class NonZeroFilter(Node):
    # forwards key_vel -> key_vel_filtered only when the command is non-zero, so idle teleop zeros don't win the mux
    def __init__(self):
        super().__init__('nonzero_filter')
        self.pub = self.create_publisher(Twist, 'key_vel_filtered', 10)
        self.create_subscription(Twist, 'key_vel', self.cb, 10)

    def cb(self, m):
        v = (m.linear.x, m.linear.y, m.linear.z, m.angular.x, m.angular.y, m.angular.z)
        if any(v):
            self.pub.publish(m)


def main():
    rclpy.init()
    rclpy.spin(NonZeroFilter())
