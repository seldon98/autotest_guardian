import uiautomator2 as u2
import time
from datetime import datetime, timedelta
import logging
import os
from datetime import datetime

from scripts.regsetup import description

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 指定目标路径（可以是绝对路径或相对路径）
target_path = rf"E:\Jenkins\SWS_Git\guardian\logs\screen\{timestamp}"  # 替换为你的路径

# 创建文件夹（如果路径中的父目录不存在，会自动创建）
os.makedirs(target_path, exist_ok=True)  # exist_ok=True 表示文件夹存在时不报错


class TestBluetoothConnect:

    def disconnect(self, d):
        try:
            # 点击 Hypershell 主入口
            time.sleep(5)
            d(description="number 2").click()
            time.sleep(3)
        except Exception as e:
            print(f"Error clicking Hypershell entrance: {e}")
            # 可根据需要决定是否终止流程
            # return False

        try:
            # 点击坐标位置
            d.click(0.842, 0.183)
            time.sleep(5)
        except Exception as e:
            print(f"Error clicking coordinates: {e}")

        try:
            # 查找并操作元素
            elements = d(className="android.view.View", index="8")
            if elements.exists():
                elements.click()
                time.sleep(2)
        except Exception as e:
            print(f"Error handling dynamic elements: {e}")

        try:
            # 解绑操作
            if d(description="解绑").exists():
                d(description="解绑").click()
                time.sleep(5)

            if d(description="搜寻设备").exists():
                logging.info("disconnect success!")

        except Exception as e:
            print(f"Error during unbinding: {e}")

    def connet(self, d):
        try:
            # 点击设备主入口
            if not d(description="搜寻设备").exists(timeout=5):
                logging.warning("未找到'搜寻设备'入口")
                return False

            d(description="搜寻设备").click()
            time.sleep(5)

            start_time = datetime.now()
            timeout = 30  # 设置超时变量

            while (datetime.now() - start_time).total_seconds() < timeout:
                if d(description="number 2").exists(timeout=1):
                    # 添加点击重试逻辑
                    for _ in range(3):
                        try:
                            d.click(0.816, 0.409)
                            break
                        except Exception as e:
                            logging.warning(f"点击失败，重试 {_ + 1}/3")
                            time.sleep(1)

                    # 使用显式等待
                    if d(description="重新检测").wait(timeout=10):
                        d(description="取消").click()
                        logging.info("connect success!")
                        return True

                    if d(description="充电中").wait(timeout=10):
                        d(description="确认").click()
                        logging.info("connect success!")
                        return True

                    if d(description="number 2").exists():
                        logging.info("connect success!")
                        return True

                time.sleep(1)  # 添加轮询间隔

            # 超时处理
            d.screenshot(os.path.join(target_path, "connect_timeout.jpg"))
            logging.error(f"连接超时({timeout}s)")
            return False

        except Exception as e:
            logging.error(f"连接过程异常: {str(e)}")
            d.screenshot(os.path.join(target_path, "connect_error.jpg"))
            return False

    def test_execution(self, case_config):

        # 初始化设备连接
        d = u2.connect('NAB0220730025203')

        d.app_stop('com.hypershell.hypershell')

        # 确保应用运行状态
        if not d.app_wait("com.hypershell.hypershell", timeout=10):
            print("应用未启动，正在启动...")
            d.app_start('com.hypershell.hypershell')
            time.sleep(5)

        if d(description="取消").exists():
            d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\{timestamp}\DetectAnomalies.jpg")  # 修正路径
            d(description="取消").click()
            print("已点击取消按钮")

        if d(description="充电中"):
            d(description="确认").click()


        self.disconnect(d)

        if d(description="取消").exists():
            d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\{timestamp}\DetectAnomalies.jpg")  # 修正路径
            d(description="取消").click()
            print("已点击取消按钮")

        if d(description="充电中"):
            d(description="确认").click()


        time.sleep(5)

        if self.connet(d):
            pass
        else:
            assert False

