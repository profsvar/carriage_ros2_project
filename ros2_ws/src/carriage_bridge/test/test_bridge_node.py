import time
import unittest
from unittest.mock import MagicMock, patch

import rclpy

# Мокаем pymodbus перед импортом самой ноды
import sys
sys.modules['pymodbus'] = MagicMock()
sys.modules['pymodbus.client'] = MagicMock()
sys.modules['pymodbus.client.sync'] = MagicMock()

# В проекте scripts находится в корне пакета, добавляем путь
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from carriage_bridge_node import CarriageBridgeNode


class TestCarriageBridgeSimMode(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        # Принудительно отключаем MODBUS_OK для чистой симуляции (если нужно)
        with patch('carriage_bridge_node.MODBUS_OK', False):
            self.node = CarriageBridgeNode()

    def tearDown(self):
        self.node.destroy_node()

    def test_node_initializes(self):
        """Нода должна создаться без исключений в режиме симуляции."""
        self.assertIsNotNone(self.node)

    def test_publisher_exists(self):
        """Должен существовать publisher на /carriage/joint_states."""
        self.assertIsNotNone(self.node.js_pub)

    def test_sim_position_increases(self):
        """В режиме симуляции позиция должна нарастать после вызова poll()."""
        initial_pos = self.node._sim_pos
        time.sleep(0.05)
        self.node.poll()
        self.assertGreater(self.node._sim_pos, initial_pos)
        self.assertEqual(self.node._last_linear_speed, 0.005)

    def test_sim_angle_oscillates(self):
        """Скорость осциллятора в симуляции должна быть 0.1"""
        self.node.poll()
        self.assertEqual(self.node._last_osc_speed, 0.1)

    def test_fail_counter_resets_on_reconnect(self):
        """Счётчик ошибок должен сбрасываться при успешном переподключении (когда MODBUS_OK=True)."""
        # Пересоздаём ноду с включенным Modbus
        with patch('carriage_bridge_node.MODBUS_OK', True):
            node_modbus = CarriageBridgeNode()
            
            node_modbus.client = MagicMock()
            # Эмулируем ошибку при чтении
            node_modbus.client.read_input_registers.side_effect = RuntimeError("timeout")
            # Эмулируем успешное подключение
            node_modbus.client.connect.return_value = True
            
            # Ставим счетчик так, чтобы следующая ошибка вызвала реконнект
            node_modbus._modbus_fail_count = node_modbus._MODBUS_FAIL_THRESHOLD - 1
            
            # Производим полл (чтение падает -> счетчик увеличивается -> порог достигнут -> реконнект)
            node_modbus.poll()
            
            # После переподключения счетчик должен сброситься на 0
            self.assertEqual(node_modbus._modbus_fail_count, 0)
            
            node_modbus.destroy_node()

if __name__ == '__main__':
    unittest.main()
