import rclpy
from rclpy.node import Node
import message_filters
from sensor_msgs.msg import Image, PointCloud2
from geometry_msgs.msg import PoseStamped
# from nav_msgs.msg import Odometry # Odometry를 사용할 경우

class MapBuilderNode(Node):
    def __init__(self):
        super().__init__('map_builder_node')

        # 1. 각 토픽에 대한 Subscriber 생성
        # 실제 사용하는 토픽 이름으로 변경해야 합니다.
        self.rgb_sub = message_filters.Subscriber(self, Image, '/camera/color/image_raw')
        self.depth_sub = message_filters.Subscriber(self, Image, '/camera/aligned_depth_to_color/image_raw')
        # self.points_sub = message_filters.Subscriber(self, PointCloud2, '/camera/depth/color/points') # 포인트 클라우드를 직접 쓴다면
        self.pose_sub = message_filters.Subscriber(self, PoseStamped, '/your_camera_pose_topic') # 실제 포즈 토픽으로 변경

        # 2. ApproximateTimeSynchronizer 설정
        # slop: 메시지 간의 타임스탬프 차이를 얼마나 허용할지 (초 단위)
        self.time_synchronizer = message_filters.ApproximateTimeSynchronizer(
            [self.rgb_sub, self.depth_sub, self.pose_sub], # 동기화할 Subscriber 리스트
            queue_size=10,  # 큐 사이즈
            slop=0.1        # 0.1초 이내의 타임스탬프 차이를 허용
        )

        # 3. 동기화된 메시지를 처리할 콜백 함수 등록
        self.time_synchronizer.registerCallback(self.synchronized_callback)

        self.get_logger().info('Map Builder Node has been started and is waiting for synchronized messages.')

    def synchronized_callback(self, rgb_msg, depth_msg, pose_msg):
        # 이 함수는 세 토픽의 메시지가 동기화되었을 때만 호출됩니다.
        
        # 타임스탬프 확인 (디버깅용)
        rgb_stamp = rgb_msg.header.stamp.sec + rgb_msg.header.stamp.nanosec * 1e-9
        depth_stamp = depth_msg.header.stamp.sec + depth_msg.header.stamp.nanosec * 1e-9
        pose_stamp = pose_msg.header.stamp.sec + pose_msg.header.stamp.nanosec * 1e-9
        
        self.get_logger().info(
            f'Received synchronized messages:\n'
            f'  RGB Time:   {rgb_stamp:.4f}\n'
            f'  Depth Time: {depth_stamp:.4f}\n'
            f'  Pose Time:  {pose_stamp:.4f}'
        )

        # ------------------------------------------------------------------
        # 여기에 글로벌 맵 생성 로직을 구현합니다.
        #
        # 1. (필요시) cv_bridge를 사용하여 ROS Image 메시지를 OpenCV 이미지로 변환
        # 2. pose_msg (카메라의 글로벌 포즈)를 사용하여
        # 3. RGB 이미지와 Depth 이미지를 글로벌 좌표계의 3D 포인트 클라우드로 변환
        # 4. 이 포인트 클라우드를 글로벌 맵(예: OctoMap, Voxel Grid 등)에 누적
        # ------------------------------------------------------------------
        pass


def main(args=None):
    rclpy.init(args=args)
    map_builder_node = MapBuilderNode()
    rclpy.spin(map_builder_node)
    map_builder_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()