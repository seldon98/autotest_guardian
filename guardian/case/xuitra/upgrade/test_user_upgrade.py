import uiautomator2 as u2
from uiautomator2 import exceptions
import time
from datetime import datetime, timedelta
import logging
import os

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 时间戳 & 截图路径
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
target_path = os.path.join("E:\\Jenkins\\SWS_Git\\autotest_guardian\\guardian\\logs\\screen", timestamp)
os.makedirs(target_path, exist_ok=True)


class TestUserUpgrade:

    def safe_click(self, d, timeout=10, **selector):
        """等待并点击指定元素，失败则抛异常和截图"""
        if not d(**selector).wait(timeout=timeout):
            screenshot = os.path.join(target_path, f"element_not_found_{selector}.jpg")
            d.screenshot(screenshot)
            raise RuntimeError(f"元素未找到: {selector}")
        d(**selector).click()

    def enter_upgrade(self, d):
        time.sleep(5)

        # 等待页面稳定，通过等待目标元素
        if not d(description="debug 1").wait(timeout=10.0):
            raise RuntimeError("主入口元素 [debug 1] 未加载完成")

        self.safe_click(d, description="debug 1")
        time.sleep(3)

        d.click(0.842, 0.183)
        time.sleep(5)

        self.safe_click(d, description="升级")
        time.sleep(3)

        if d(description="固件重刷确认").exists():
            self.safe_click(d, description="重刷")
            time.sleep(3)
            d.swipe_ext("up")
            time.sleep(3)
            self.safe_click(d, description="重刷")
            time.sleep(3)
            self.safe_click(d, description="继续")
            time.sleep(3)
            self.safe_click(d, description="升级")
        else:
            d.swipe_ext("up")
            time.sleep(2)
            self.safe_click(d, description="升级")
            time.sleep(3)

            if d(description="更新前请注意").exists():
                self.safe_click(d, description="继续")
                time.sleep(3)

            if d(description="固件重刷确认").exists():
                self.safe_click(d, description="重刷")
                time.sleep(3)
                d.swipe_ext("up")
                time.sleep(3)
                self.safe_click(d, description="继续")
                time.sleep(3)
                self.safe_click(d, description="升级")

            if d(description="确定现在更新吗？").exists():
                self.safe_click(d, description="升级")

        time.sleep(3)

        if d(description="请在手机上保持蓝牙开启,并在更新时保持应用在前台").exists():
            logging.info("进入升级流程")

    def safe_print_description(self, description):
        """Safely print the element's description."""
        try:
            if description:
                logging.info(f"Element Description 升级进度: {description}")
        except Exception as e:
            logging.error(f"Failed to print description: {e}")

    def monitor_view_descriptions(self, d, duration_minutes=10):
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        logging.info(f"开始监控，持续到 {end_time.strftime('%H:%M:%S')}")

        while datetime.now() < end_time:
            try:
                elements = d(packageName="com.hypershell.hypershell", index=0)

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
                    d.screenshot(os.path.join(target_path, "upgrade_success.jpg"))
                    return True

                time.sleep(2)

            except Exception as e:
                # 如果是UiObjectNotFoundError，我们已经在内部处理了，所以这里捕获的是其他异常
                logging.exception(f"测试执行失败: {e}")
                return False

        logging.error("升级过程超时")
        return False

    def test_execution(self, case_config):
        try:
            self.d = u2.connect('NAB0220730025203')  # 初始化 self.d

            self.d.app_stop('com.hypershell.hypershell')
            if not self.d.app_wait("com.hypershell.hypershell", timeout=10):
                logging.info("应用未启动，正在启动...")
                self.d.app_start('com.hypershell.hypershell')
                time.sleep(15)

            if self.d(description="取消").exists():
                self.d.screenshot(os.path.join(target_path, "DetectAnomalies.jpg"))
                self.d(description="取消").click()
                logging.info("已点击取消按钮")

            if self.d(description="充电/放电中").exists():
                self.d(description="确认").click()

            self.enter_upgrade(self.d)

            if self.monitor_view_descriptions(self.d, duration_minutes=10):  # 传递 self.d
                logging.info('升级成功')
                self.d.screenshot(os.path.join(target_path, "upgradeSuccess.jpg"))
            else:
                logging.error('升级失败')
                self.d.screenshot(os.path.join(target_path, "upgradeFail.jpg"))
                assert False

        except Exception as e:
            logging.exception(f"测试执行失败: {e}")
            self.d.screenshot(os.path.join(target_path, "unexpected_error.jpg"))
