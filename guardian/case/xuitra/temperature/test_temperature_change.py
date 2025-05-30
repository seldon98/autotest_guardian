import serial
import time
import logging
import re
import matplotlib
matplotlib.use('Agg')  # 非GUI后端，适用于 Jenkins 等无图形界面环境
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 串口配置
ser = serial.Serial(
    port='COM6',
    baudrate=3000000,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

# 解析串口返回的温度信息
def parse_temperature_response(response: str) -> dict:
    data = {}
    for line in response.strip().splitlines():
        match = re.match(r'(\w+):\s*(\d+)', line)
        if match:
            key, value = match.groups()
            data[key] = int(value)
    return data

# 绘制趋势图（时间 vs 温度）
def plot_temperature_trend(timestamps: list[str], data: list[int], title: str, output_dir: str):
    if not data or not timestamps or len(data) != len(timestamps):
        logging.warning(f"{title} 数据与时间戳不匹配，无法绘图")
        return

    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, data, marker='o', linestyle='-', color='blue', label=title)
    plt.title(f'{title} Temperature Trend')
    plt.xlabel('Time')
    plt.ylabel('Temperature (℃)')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    file_path = os.path.join(output_dir, f"{title.lower()}_trend.png")
    plt.savefig(file_path)
    plt.close()
    logging.info(f"{title} 曲线图保存至: {file_path}")

class TestTemperatureChange:

    def send_command(self, command: str, wait_time: float = 2.0) -> str:
        try:
            if not ser.is_open:
                ser.open()

            full_cmd = command.strip().encode('utf-8') + b'\n'
            ser.write(full_cmd)
            logging.info(f"发送指令: {command}")

            time.sleep(wait_time)

            response = ser.read_all().decode('utf-8', errors='ignore')
            logging.info(f"回包内容:\n{response}")
            return response
        except Exception as e:
            logging.error(f"发送指令异常: {e}")
            assert False

    def test_execution(self, case_config=None):
        try:
            if not ser.is_open:
                ser.open()

            sample_times = 20
            collected_data = {'left': [], 'right': [], 'cell': [], 'fet': []}
            timestamps = []

            duration_seconds = 1 * 60  # 30 分钟
            sampling_interval = 4  # 每 4 秒采集一次（0.25Hz）

            start_time = time.time()

            while (time.time() - start_time) < duration_seconds:
                current_time = datetime.now()
                timestamps.append(current_time.strftime("%H:%M:%S"))  # 记录当前时间（时:分:秒）

                raw_response = self.send_command('get_tem', 0.5)
                parsed = parse_temperature_response(raw_response)
                logging.info(f"当前采样数据: {parsed}")

                for key in collected_data:
                    if key in parsed:
                        collected_data[key].append(parsed[key])

                time.sleep(sampling_interval)

            ser.close()

            # 创建时间戳文件夹
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            output_dir = os.path.join('.', 'image', timestamp)
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"图像将保存至: {output_dir}")

            # 生成温度趋势图
            for key, values in collected_data.items():
                plot_temperature_trend(timestamps, values, title=key.upper(), output_dir=output_dir)

        except Exception as e:
            logging.error(f"测试执行异常: {e}")
            assert False

