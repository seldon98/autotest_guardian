import logging
import requests
import os


class TestDownloadFirmware:  # 修正类名拼写

    def get_latest_firmware_from_api(self, api_url):
        """通过 API 获取最新固件信息"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # 部分API需要User-Agent
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()

            # 调试日志：记录响应类型和内容样例
            logging.info(f"API状态码: {response.status_code}")
            logging.debug(f"响应头: {response.headers}")
            logging.debug(f"内容样例: {response.content[:100]}")  # 打印前100字节

            # 检查是否为JSON
            if 'application/json' in response.headers.get('Content-Type', ''):
                firmware_info = response.json()
                return firmware_info.get('firmware_url', api_url)  # 默认返回原URL
            else:
                logging.info("响应非JSON，可能直接返回固件文件")
                return api_url  # 直接使用API URL作为下载地址

        except requests.RequestException as e:
            logging.error(f"API请求失败: {e}")
            return None

    def download_firmware(self, firmware_url, save_path):
        """下载固件文件并保存到指定路径"""
        try:
            if os.path.exists(save_path):
                logging.info(f"文件已存在，跳过下载: {save_path}")
                return True

            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 流式下载大文件
            with requests.get(firmware_url, stream=True) as response:
                response.raise_for_status()
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            logging.info(f"固件下载成功: {save_path}")
            return True
        except Exception as e:
            logging.error(f"下载失败: {e}")
            return False


    def test_execution(self):


        """测试执行入口 主板固件API"""
        #服务器当前主板第二新固件
        api_url = "http://8.217.150.31:8090/webDevice/downloadFirmwareTest?type=1&firmwareType=1&randomString=Hypershell2024&index=1"
        firmware_url = self.get_latest_firmware_from_api(api_url)

        if not firmware_url:
            logging.error("无法获取固件URL")
            return

        save_path = "./case/xuitra/boot/esp32/stable/firmware.bin"
        os.remove(save_path)
        if self.download_firmware(firmware_url, save_path):
            logging.info("测试通过")
        else:
            logging.error("测试失败")
            assert False

        # 服务器当前主板最新固件
        api_url = "http://8.217.150.31:8090/webDevice/downloadFirmwareTest?type=1&firmwareType=1&randomString=Hypershell2024&index=0"
        firmware_url = self.get_latest_firmware_from_api(api_url)

        if not firmware_url:
            logging.error("无法获取固件URL")
            return

        save_path = "./case/xuitra/boot/esp32/test/firmware.bin"
        os.remove(save_path)
        if self.download_firmware(firmware_url, save_path):
            logging.info("测试通过")
        else:
            logging.error("测试失败")
            assert False

