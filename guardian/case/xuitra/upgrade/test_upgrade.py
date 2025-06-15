import uiautomator2 as u2
from uiautomator2 import exceptions
import time
from datetime import datetime, timedelta
import logging
import os
import pytest

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 时间戳 & 截图路径
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
target_path = os.path.join("E:\\Jenkins\\SWS_Git\\autotest_guardian\\guardian\\logs\\screen", timestamp)
os.makedirs(target_path, exist_ok=True)


class TestUpgrade:

    def setup_method(self):
        """Setup for each test."""
        self.d = u2.connect('NAB0220730025203')
        self.d.app_stop('com.hypershell.hypershell')
        if not self.d.app_wait("com.hypershell.hypershell", timeout=10):
            logging.info("应用未启动，正在启动...")
            self.d.app_start('com.hypershell.hypershell')
            time.sleep(10)

        # Handle any pop-ups or issues before continuing with the test
        if self.d(description="取消").exists():
            self.d(description="取消").click()
            time.sleep(1)
        if self.d(description="充电/放电中").exists():
            self.d(description="确认").click()
            time.sleep(1)
        if self.d(description="噢唷！").exists():
            self.d(description="取消").click()
            time.sleep(1)

    def safe_print_description(self, description):
        """Safely print the element's description."""
        try:
            if description:
                logging.info(f"Element Description 升级进度: {description}")
        except Exception as e:
            logging.error(f"Failed to print description: {e}")

    def enter_upgrade(self, d):
        if not d(description="固件测试平台").wait(timeout=10.0):
            logging.error("主入口元素 固件测试平台 未加载完成")
            return False
        else:
            try:
                d(description="固件测试平台").click()
                logging.info('进入固件测试平台')
                time.sleep(1)
                logging.info('选择电机固件')
                d.click(0.884, 0.401)
                time.sleep(1)
                logging.info('选择主板固件')
                d(description="主板").click()
                time.sleep(1)
                d.click(0.896, 0.393)
                time.sleep(1)
                logging.info('版本选择完成')
                d(description="去升级").click()
                time.sleep(1)

                if d(description="固件升级").exists():
                    logging.info('进入升级！')

                    if self.monitor_view_descriptions(d, duration_minutes=10):
                        return True
                    else:
                        return False
                else:
                    logging.error('进入升级失败')
                    d.screenshot(os.path.join(target_path, "enterupgradeError.jpg"))
                    return False
            except Exception as e:
                logging.error(f"重连失败: {e}")
                return False

    def monitor_view_descriptions(self, d, duration_minutes=10):
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        logging.info(f"开始监控，持续到 {end_time.strftime('%H:%M:%S')}")

        while datetime.now() < end_time:
            try:
                elements = d( packageName="com.hypershell.hypershell", index = 0)

                if not elements.exists:
                    logging.info("未找到目标元素")
                    time.sleep(5)
                    continue

                for elem in elements:
                    try:
                        desc = elem.info.get('contentDescription')
                        self.safe_print_description(desc)
                    except exceptions.UiObjectNotFoundError as e:
                        logging.warning(f"元素在获取信息时消失: {e}")
                        continue  # 跳过当前元素，继续下一个

                # 检查升级失败或成功
                if d(description="固件更新失败").exists():
                    logging.error("检测到固件更新失败")
                    d.screenshot(os.path.join(target_path, "upgrade_error.jpg"))
                    return False

                if d(description="固件更新成功").exists():
                    logging.info("升级成功")
                    self.d.screenshot(os.path.join(target_path, "upgrade_success.jpg"))
                    return True

                time.sleep(2)

            except Exception as e:
                # 如果是UiObjectNotFoundError，我们已经在内部处理了，所以这里捕获的是其他异常
                logging.exception(f"测试执行失败: {e}")
                return False

        logging.error("升级过程超时")
        return False

    def test_execution(self):
        try:
            assert self.enter_upgrade(self.d), "固件升级失败"
        except Exception as e:
            logging.exception(f"测试执行失败: {e}")
            self.d.screenshot(os.path.join(target_path, "unexpected_error.jpg"))
            assert False
