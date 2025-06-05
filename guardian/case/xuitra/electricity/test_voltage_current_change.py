import re
import os
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import logging
from datetime import datetime, date, time, timedelta

# 正则表达式匹配时间和阶段状态
TIME_PATTERN = re.compile(r"(\d{2}:\d{2}:\d{2}:\d{3})")
CHARGE_STATE_PATTERN = re.compile(r"charge_state\s*=\s*(\d),\s*(.+)")

# 时间戳标记
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 需要提取的字段
FIELDS = ["rawsoc", "soc", "2366_bat_vlotage", "2366_bat_cur", "2366_sys_cur", "z50_c", "z50_v"]

# 为每个字段构建匹配正则表达式
field_patterns = {
    field: re.compile(rf"{field}\s*[:=]\s*(-?\d+)")
    for field in FIELDS
}

# 不同充电阶段对应的颜色
CHARGE_STAGE_COLORS = {
    "constant current": "#B3E5FC",
    "constant voltage": "#FFCDD2",
    "trickle": "#C8E6C9",
}


class TestVoltageCurrentChange:

    def parse_log_file(self, file_path):
        data = {field: [] for field in FIELDS}
        charge_stages = []
        current_stage = None

        # 从文件名中提取日期
        filename = os.path.basename(file_path)
        date_match = re.search(r"(\d{4})_(\d{2})_(\d{2})", filename)
        if date_match:
            base_date = date(*map(int, date_match.groups()))
        else:
            base_date = date.today()

        current_date = base_date
        prev_ts = None

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                time_match = TIME_PATTERN.search(line)
                if not time_match:
                    continue

                try:
                    time_str = time_match.group(1)
                    # 解析时间部分（不含日期）
                    t = datetime.strptime(time_str, "%H:%M:%S:%f").time()

                    # 处理跨天情况
                    if prev_ts:
                        # 如果当前时间小于前一个时间戳的时间部分，说明已跨天
                        if t < prev_ts.time():
                            current_date += timedelta(days=1)

                    # 组合日期和时间
                    ts = datetime.combine(current_date, t)
                    prev_ts = ts

                except ValueError:
                    continue

                for field, pattern in field_patterns.items():
                    match = pattern.search(line)
                    if match:
                        value = int(match.group(1))
                        data[field].append((ts, value))

                if "charge_state" in line:
                    match = CHARGE_STATE_PATTERN.search(line)
                    if match:
                        stage_label = match.group(2).strip()
                        if current_stage:
                            current_stage["end"] = ts
                            charge_stages.append(current_stage)
                        current_stage = {"start": ts, "label": stage_label}

        if current_stage and "end" not in current_stage:
            current_stage["end"] = ts
            charge_stages.append(current_stage)

        return data, charge_stages

    def plot_time_series(self, field, time_value_pairs, output_dir, charge_stages):
        if not time_value_pairs:
            print(f"跳过字段 {field}（无数据）")
            return

        times, values = zip(*time_value_pairs)
        plt.figure(figsize=(10, 4))

        for stage in charge_stages:
            color = CHARGE_STAGE_COLORS.get(stage["label"], "#E0E0E0")
            plt.axvspan(stage["start"], stage["end"], alpha=0.2, color=color, label=stage["label"])

        plt.plot(times, values, marker='o', linestyle='-', color='blue', label=field)

        plt.title(f"{field} 时间序列变化图")
        plt.xlabel("时间")
        plt.ylabel(field)
        plt.grid(True)
        plt.gcf().autofmt_xdate()

        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())

        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{field}_time_series.png")
        plt.savefig(out_path)
        plt.close()
        logging.info(f"图已保存：{out_path}")

    def test_execution(self, case_config=None):
        log_file = "E:\\log\\COM10_2025_05_30.18.27.50.514.txt"
        output_dir = rf".\\image\\{timestamp}"
        print(f"📄 日志路径: {log_file}")
        print(f"📂 图片输出目录: {output_dir}")

        extracted_data, charge_stages = self.parse_log_file(log_file)

        for field, time_value_pairs in extracted_data.items():
            logging.info(f"📊 绘图字段: {field}，数据点数量: {len(time_value_pairs)}")
            self.plot_time_series(field, time_value_pairs, output_dir, charge_stages)
