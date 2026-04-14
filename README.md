# Carriage ROS2 Bridge

Данный проект представляет собой ROS2-мост для управления сварочной кареткой на базе контроллера STM32F373. Мост реализован на языке Python с использованием протокола Modbus RTU и предназначен для запуска на Raspberry Pi (RPI) внутри Docker-контейнера.

## Структура проекта

- `ros2_ws/` — ROS2 воркспейс с пакетом `carriage_bridge`.
- `run_carriage_bridge.sh` — скрипт для сборки и запуска контейнера.
- `get-docker.sh` — скрипт для автоматической установки Docker на RPI.
- `config/cyclonedds_rpi.xml` — конфигурация DDS, оптимизированная для Raspberry Pi.

---

## Руководство по запуску на Raspberry Pi

### 1. Подготовка железа (UART)

Для работы Modbus через встроенный UART Raspberry Pi:
1. Выполните `sudo raspi-config`.
2. Перейдите в **Interface Options** -> **Serial Port**.
3. На вопрос "Would you like a login shell to be accessible over serial?" ответьте **No**.
4. На вопрос "Would you like the serial port hardware to be enabled?" ответьте **Yes**.
5. Перезагрузите устройство: `sudo reboot`.

### 2. Установка окружения

Если Docker еще не установлен, используйте скрипт в корне проекта:
```bash
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Перезайдите в систему (re-login)
```

### 3. Клонирование и запуск

```bash
git clone https://github.com/profsvar/carriage_ros2_project.git
cd carriage_ros2_project

# Сделайте скрипт исполняемым и запустите его
chmod +x run_carriage_bridge.sh
./run_carriage_bridge.sh
```

---

## Руководство по проверке работоспособности

После запуска контейнера выполните следующие шаги для тестов:

### Шаг 1: Проверка связи Modbus
Зайдите в работающий контейнер и запустите диагностический скрипт:
```bash
docker exec -it ros2_carriage bash
# Внутри контейнера:
python3 /ros2_ws/src/carriage_bridge/scripts/test_modbus_link.py
```
*Ожидаемый результат: сообщение "Modbus Link OK".*

### Шаг 2: Проверка данных в ROS2
Убедитесь, что нода публикует данные о состоянии каретки:
```bash
ros2 topic echo /carriage/joint_states
```
*Вы должны увидеть структуру JointState с позициями `carriage_joint` и `oscillator_joint`.*

### Шаг 3: Удаленная визуализация (RViz2)
Если ваш ПК находится в одной сети с RPI:
1. Установите `ROS_DOMAIN_ID=42`.
2. Запустите `rviz2`.
3. Добавьте модуль **RobotModel** и подпишитесь на топик `/carriage/joint_states`.

---

## Зависимости
Проект использует:
- ROS2 Humble
- `pymodbus>=3.0`
- `CycloneDDS`
