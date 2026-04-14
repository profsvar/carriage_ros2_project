#!/usr/bin/env python3
"""
test_modbus_link.py — быстрая проверка Modbus RTU-соединения RPi ↔ STM32F373.

Запускать на RPi (не в WSL), в том же venv, где установлен pymodbus.

Пример:
    python test_modbus_link.py --port /dev/ttyAMA0 --baud 115200 --slave 0xCA
"""
import argparse
from typing import Optional

import sys

try:
    from pymodbus.client import ModbusSerialClient
except ImportError:
    try:
        from pymodbus.client.sync import ModbusSerialClient
    except ImportError:
        print("ERROR: module 'pymodbus' is not installed. Please install it (e.g. pip install pymodbus).")
        sys.exit(1)

REG_MBADDR = 0
REG_LINESP = 9
REG_MILAGE = 4
REG_WELD_MILAGE = 5
REG_WELD_MODE = 6


def read_holding(client: ModbusSerialClient, addr: int, count: int, unit: int) -> Optional[list]:
    rr = client.read_holding_registers(addr, count=count, slave=unit)
    if rr.isError() or not getattr(rr, "registers", None):
        print(f"HR{addr}: read error ({rr})")
        return None
    return rr.registers


def read_input(client: ModbusSerialClient, addr: int, count: int, unit: int) -> Optional[list]:
    rr = client.read_input_registers(addr, count=count, slave=unit)
    if rr.isError() or not getattr(rr, "registers", None):
        print(f"IR{addr}: read error ({rr})")
        return None
    return rr.registers


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Modbus RTU link RPi ↔ STM32F373.")
    parser.add_argument("--port", "-p", default="/dev/serial0")
    parser.add_argument("--baud", "-b", type=int, default=115200)
    parser.add_argument("--slave", "-s", type=lambda x: int(x, 0), default=0xCA)
    parser.add_argument("--timeout", "-t", type=float, default=0.5)
    args = parser.parse_args()

    print("=== Modbus RTU link test RPi ↔ STM32F373 ===")
    print(f"Port    : {args.port}")
    print(f"Baud    : {args.baud}")
    print(f"Slave   : {args.slave} (dec), 0x{args.slave:02X} (hex)")
    print(f"Timeout : {args.timeout}s")
    print("==========================================")

    client = ModbusSerialClient(
        port=args.port,
        baudrate=args.baud,
        timeout=args.timeout,
    )

    if not client.connect():
        print("ERROR: Не удалось открыть Modbus-подключение.")
        return 1

    try:
        mbaddr_regs = read_holding(client, REG_MBADDR, 1, args.slave)
        if mbaddr_regs is not None:
            mbaddr = mbaddr_regs[0]
            print(f"HR0 (MBADDR): {mbaddr} (dec), 0x{mbaddr:02X} (hex)")

        linesp_regs = read_holding(client, REG_LINESP, 1, args.slave)
        if linesp_regs is not None:
            raw_linesp = linesp_regs[0]
            print(f"HR9 (LINESP): raw={raw_linesp}")

        ir_regs = read_input(client, REG_MILAGE, 3, args.slave)
        if ir_regs is not None and len(ir_regs) >= 3:
            print(f"IR4 (MILAGE)      : {ir_regs[0]}")
            print(f"IR5 (WELD_MILAGE) : {ir_regs[1]}")
            print(f"IR6 (WELD_MODE)   : {ir_regs[2]}")

        print("Готово.")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
