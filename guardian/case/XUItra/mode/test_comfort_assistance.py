import logging
import uiautomator2 as u2
import time
from datetime import datetime
import os

from scripts.regsetup import description

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 指定目标路径（可以是绝对路径或相对路径）
target_path = rf"E:\Jenkins\SWS_Git\guardian\logs\screen\{timestamp}"  # 替换为你的路径

# 创建文件夹（如果路径中的父目录不存在，会自动创建）
os.makedirs(target_path, exist_ok=True)  # exist_ok=True 表示文件夹存在时不报错


class TestComfortAssistance:

    def leftSwipeMin(self, d, element, percentValue):
        # 使用组合条件定位元素（优先）

        if element.exists():
            # 方法1：直接点击元素
            element.click()

            # 方法2：滑动操作（根据 scrollable=True）
            element.swipe("left", steps=100)  # 向左滑动

            time.sleep(2)

            element.swipe("left", steps=100)  # 向左滑动

            time.sleep(2)

            element.swipe("left", steps=100)  # 向左滑动

            time.sleep(2)

            logging.info("助力强度为::"+percentValue.info['contentDescription']+"%")

            return percentValue.info['contentDescription']

        else:
            logging.error("元素未找到，尝试滚动到可视区域")
            # 若元素在 ScrollView 中需要滚动
            d(scrollable=True).scroll.to(className="android.view.View", index=18)
            return "No"


    def leftSwipeDown(self, element, percentValue):

        element.click()

        time.sleep(2)

        # 方法2：滑动操作（根据 scrollable=True）
        element.swipe("left", steps=5)

        time.sleep(2)

        return percentValue.info['contentDescription']

    def rightSwipeMax(self, d, element, percentValue):

        if element.exists():
            # 方法1：直接点击元素
            element.click()

            # 方法2：滑动操作（根据 scrollable=True）
            element.swipe("right", steps=100)  # 向左滑动

            time.sleep(2)

            element.swipe("right", steps=100)  # 向左滑动

            time.sleep(2)

            element.swipe("right", steps=100)  # 向左滑动

            time.sleep(2)

            logging.info("Description 属性值:"+percentValue.info['contentDescription']+"%")

            return percentValue.info['contentDescription']

        else:
            logging.error("元素未找到，尝试滚动到可视区域")
            # 若元素在 ScrollView 中需要滚动
            d(scrollable=True).scroll.to(className="android.view.View", index=18)

            return "No"


    def rightSwipeUp(self, element, percentValue):

        element.click()

        time.sleep(2)

        # 方法2：滑动操作（根据 scrollable=True）
        element.swipe("right", steps=5)

        time.sleep(2)

        return percentValue.info['contentDescription']



    def perpare(self, d):

        d.app_stop('com.hypershell.hypershell')

        time.sleep(3)

        d.app_start('com.hypershell.hypershell')

        time.sleep(10)

        # 获取屏幕尺寸
        width, height = d.window_size()

        # 从屏幕中间 80% 位置下滑到中间 20% 位置（模拟手指下滑）
        start_x = width * 0.5  # 横向中点
        start_y = height * 0.8  # 纵向 80% 位置（靠近底部）
        end_y = height * 0.2  # 纵向 20% 位置（靠近顶部）

        # 执行滑动（duration 控制滑动速度，单位：秒）
        d.swipe(start_x, start_y, start_x, end_y, duration=0.5)

        time.sleep(3)

        if d(description="取消").exists():
            d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\{timestamp}\DetectAnomalies.jpg")  # 修正路径
            d(description="取消").click()
            logging.info("已点击取消按钮")
            time.sleep(2)

        if d(description="舒适").exists():
            d(description="舒适").click()
            time.sleep(2)



    def test_execution(self, case_config):

        logging.info("舒适模式下的助力设置")

        d = u2.connect('NAB0220730025203')

        self.perpare(d)

        # 使用组合条件定位元素（优先）
        element = d(
            className="android.view.View",
            packageName="com.hypershell.hypershell",
            index=19  # 根据属性中的 index=18
        )

        percentValue = d(
            className="android.view.View",
            packageName="com.hypershell.hypershell",
            index="16"
        )

        # Flag  = True
        #
        # logging.info("设置舒适模式助力强度至1%")
        # MinValue = self.leftSwipeMin(d, element, percentValue)
        #
        # if MinValue == "No":
        #     logging.error("助力设置至1%失败")
        #     Flag = False
        # else:
        #     logging.info("当前助力强度为: " + str(MinValue) + "%")
        #
        # i = 1
        #
        # while i < 6:
        #
        #     logging.info("助力强度为:" + str(i * 20) + "%")
        #
        #     up = self.rightSwipeUp(element, percentValue)
        #
        #     if up  == str(i*20):
        #         logging.info(up + "% 助力强度设置成功:")
        #     else:
        #         logging.error(str(i*20) + "% 助力强度设置失败")
        #         d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\{timestamp}\{i * 20}%%_faile.jpg")
        #         Flag = False
        #
        #     i = i + 1
        #
        # i = 1
        #
        # while i < 6:
        #
        #     up = self.leftSwipeDown(element, percentValue)
        #     logging.info(up)
        #     if up == str(100-i * 20) or (up=="1" and i ==5):
        #         logging.info(up + "% 助力强度设置成功:")
        #     else:
        #         logging.error(str(100-i * 20) + "% 助力强度设置失败")
        #         d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\{timestamp}\{100-(i*20)}%%_error.jpg")
        #         Flag = False
        #     i = i + 1
        #
        # if Flag:
        #     logging.info("舒适模式助力强度设置测试通过")
        # else:
        #     logging.error("舒适模式阻力强度设置测试异常")
        #     assert False