import logging
import uiautomator2 as u2
import time
from datetime import datetime
import os

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
target_path = rf"D:\Jenkins\SWS_Git\autotest_guardian\guardian\logs\screen\{timestamp}"
os.makedirs(target_path, exist_ok=True)


class TestComfortAssistance:

    def leftSwipeMin(self, d, element, percentValue):
        # 确保元素存在，否则滚动后重试
        if not element.exists():
            d(scrollable=True).scroll.to(className="android.view.View", index=18) # 使用resourceId更可靠
            time.sleep(2)
            if not element.exists():
                logging.error("元素未找到")
                return "No"

        element.click()
        # 多次滑动确保到最小值
        for _ in range(3):
            element.swipe("left", steps=100)  # 调整steps更快滑动
            time.sleep(1)

        current_value = percentValue.info.get('contentDescription', '0').replace('%', '')
        logging.info(f"当前助力强度: {current_value}%")
        return current_value

    def leftSwipeDown(self, element, percentValue):
        element.click()
        element.swipe("left", steps=5)
        time.sleep(1)
        return percentValue.info.get('contentDescription', '0').replace('%', '')

    def rightSwipeUp(self, element, percentValue):
        element.click()
        element.swipe("right", steps=5)
        time.sleep(1)
        logging.info(percentValue.info.get('contentDescription', '0').replace('%', ''))
        return percentValue.info.get('contentDescription', '0').replace('%', '')

    def perpare(self, d):
        d.app_stop('com.hypershell.hypershell')
        time.sleep(3)
        d.app_start('com.hypershell.hypershell')
        time.sleep(10)

        width, height = d.window_size()
        d.swipe(width * 0.5, height * 0.8, width * 0.5, height * 0.2, duration=0.5)
        time.sleep(3)

        if d(description="取消").exists():
            d.screenshot(os.path.join(target_path, "DetectAnomalies.jpg"))
            d(description="取消").click()
            logging.info("已取消异常提示")

        if d(description="舒适").exists():
            d(description="舒适").click()
            time.sleep(2)

    def test_execution(self):
        logging.info("测试舒适模式助力强度设置")
        d = u2.connect('NAB0220730025203')
        self.perpare(d)

        # 使用resourceId或其他稳定属性定位元素
        element = d(className="android.view.View", packageName="com.hypershell.hypershell",index="19")
        percentValue = d(className="android.view.View", packageName="com.hypershell.hypershell",index="16")

        logging.info("设置到最小强度1%")
        min_value = self.leftSwipeMin(d, element, percentValue)
        if min_value == "1":
            logging.info("成功设置到1%")
            d.screenshot(os.path.join(target_path, "Eco_MinValue_Success.jpg"))
        else:
            logging.error(f"设置到1%失败，当前值: {min_value}%")
            d.screenshot(os.path.join(target_path, "Eco_MinValue_Fail.jpg"))
            assert False, "无法设置到最小助力强度"

        # 测试递增
        for i in range(1, 6):
            expected = i * 20
            actual = self.rightSwipeUp(element, percentValue)
            if actual == str(expected):
                logging.info(f"{expected}% 测试通过")
            else:
                logging.error(f"{expected}% 测试失败，实际值: {actual}%")
                d.screenshot(os.path.join(target_path, f"{expected}%_Fail.jpg"))
                assert False

        # 测试递减
        for i in range(1, 6):
            expected = 100 - i * 20
            expected = 1 if expected < 1 else expected  # 处理0%情况
            actual = self.leftSwipeDown(element, percentValue)
            if actual == str(expected):
                logging.info(f"{expected}% 测试通过")
            else:
                logging.error(f"期望 {expected}%，实际 {actual}%")
                d.screenshot(os.path.join(target_path, f"{expected}%_Fail.jpg"))
                assert False

        logging.info("舒适模式主力模式测试通过")

