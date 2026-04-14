#!/usr/bin/env python3
"""
carriage_bridge_node.py — ROS2 нода-мост STM32F373 <-> ROS2 Humble
Требует: pymodbus>=3.0, rclpy, sensor_msgs, carriage_msgs
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
import time

try:
    # pymodbus >= 3.x
    from pymodbus.client import ModbusSerialClient  # type: ignore[attr-defined]
    MODBUS_OK = True
except ImportError:
    try:
        # pymodbus 2.x (класс лежит в другом модуле)
        from pymodbus.client.sync import ModbusSerialClient  # type: ignore[attr-defined]
        MODBUS_OK = True
    except ImportError:
        ModbusSerialClient = None
        MODBUS_OK = False

# Modbus holding registers
REG_MBADDR   = 0
REG_LEFTDLY  = 1
REG_RIGHTDLY = 2
REG_SINESP   = 5
REG_SINEAMPL = 6
REG_LINESP   = 9
REG_FLAGS0   = 17
REG_FLAGS1   = 20

# Modbus input registers
REG_SERIAL_NO   = 0
REG_MILAGE      = 4
REG_WELD_MILAGE = 5
REG_WELD_MODE   = 6

F_WOLK     = 1 << 0
F_ALARM    = 1 << 1
F_TORCH_EN = 1 << 2
F_IDLE_WAY = 1 << 3

class CarriageBridgeNode(Node):
    def __init__(self):
        super().__init__("carriage_bridge")
        self.declare_parameter("port", "/dev/ttyAMA0")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("slave_addr", 0xCA)
        self.declare_parameter("poll_rate", 10.0)

        port     = self.get_parameter("port").value
        baudrate = self.get_parameter("baudrate").value
        self.slave = self.get_parameter("slave_addr").value
        rate     = self.get_parameter("poll_rate").value

        self.js_pub = self.create_publisher(JointState, "/carriage/joint_states", 10)
        self.timer  = self.create_timer(1.0 / rate, self.poll)

        self.client = None
        self._modbus_port = port
        self._modbus_baudrate = baudrate
        self._modbus_fail_count = 0
        self._MODBUS_FAIL_THRESHOLD = 5

        # Последние известные скорости (для публикации в JointState)
        self._last_linear_speed = 0.0
        self._last_osc_speed = 0.0

        if MODBUS_OK:
            self.client = ModbusSerialClient(port=port,
                                             baudrate=baudrate, timeout=0.5)
            if self.client.connect():
                self.get_logger().info(f"Modbus подключён: {port} @ {baudrate}")
            else:
                self.get_logger().warn("Modbus: нет соединения — работаем в режиме симуляции")
                self.client = None
        else:
            self.get_logger().warn("pymodbus не установлен — режим симуляции")

        self._sim_pos   = 0.0
        self._sim_angle = 0.0
        self._sim_t     = time.time()

    def poll(self):
        now = time.time()
        dt  = now - self._sim_t
        self._sim_t = now

        if self.client:
            try:
                rr = self.client.read_input_registers(REG_MILAGE, 4, slave=self.slave)
                milage = 0.0
                if not rr.isError() and rr.registers and len(rr.registers) >= 1:
                    milage = rr.registers[0] / 100.0
                else:
                    raise RuntimeError("input registers read failed or empty")
                rh = self.client.read_holding_registers(REG_LINESP, 1, slave=self.slave)
                speed = 0.0
                if not rh.isError() and rh.registers and len(rh.registers) >= 1:
                    speed = rh.registers[0] / 100.0 / 60.0
                else:
                    self.get_logger().warn("Не удалось прочитать LINESP — скорость = 0")
                self._sim_pos = milage
                self._sim_angle += speed * dt
                self._last_linear_speed = speed
                self._last_osc_speed = speed  # осциллятор привязан к линейной скорости
                self._modbus_fail_count = 0
            except Exception as e:
                self._modbus_fail_count += 1
                self.get_logger().warn(f"Modbus ошибка ({self._modbus_fail_count}): {e}")
                self._sim_pos += 0.005 * dt
                self._sim_angle += 0.1 * dt
                self._last_linear_speed = 0.005
                self._last_osc_speed = 0.1
                if self._modbus_fail_count >= self._MODBUS_FAIL_THRESHOLD:
                    try:
                        self.client.close()
                        if self.client.connect():
                            self._modbus_fail_count = 0
                            self.get_logger().info("Modbus переподключен")
                        else:
                            self.get_logger().error("Modbus переподключение не удалось")
                    except Exception as reconn_e:
                        self.get_logger().error(f"Modbus reconnect failed: {reconn_e}")
        else:
            self._sim_pos   += 0.005 * dt
            self._sim_angle += 0.1 * dt
            self._last_linear_speed = 0.005
            self._last_osc_speed = 0.1

        js = JointState()
        js.header = Header()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name     = ["carriage_joint", "oscillator_joint"]
        js.position = [self._sim_pos, self._sim_angle % 0.3 - 0.15]
        js.velocity = [self._last_linear_speed, self._last_osc_speed]
        self.js_pub.publish(js)

def main(args=None):
    rclpy.init(args=args)
    node = CarriageBridgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
