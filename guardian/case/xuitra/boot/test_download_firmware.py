import logging
import requests
import os
from urllib.parse import urlsplit, unquote
import glob


# 设置保存文件的基础目录
save_base_dir = "./case/xuitra/boot"

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDownloadFirmware:

    def get_filename_from_url(self, url):
        # 从URL提取文件名
        path = urlsplit(url).path
        filename = os.path.basename(path)
        return filename

    def download_firmware(self, url, save_path):
        try:
            # 发送GET请求下载固件
            response = requests.get(url, stream=True)

            # 检查响应状态码
            if response.status_code == 200:
                # 尝试从Content-Disposition头中获取文件名
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition and 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('\"')
                else:
                    # 如果没有文件名，就从URL中提取文件名
                    filename = self.get_filename_from_url(url)

                # 拼接保存路径
                file_path = os.path.join(save_path, filename)

                # 创建保存路径目录（如果不存在的话）
                os.makedirs(save_path, exist_ok=True)

                # 将文件写入指定路径
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):  # 分块写入文件
                        f.write(chunk)

                logger.info(f"固件下载成功，文件已保存至 {file_path}")
            else:
                logger.error(f"下载失败，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"请求过程中发生错误: {e}")
        except Exception as e:
            logger.error(f"发生未知错误: {e}")

    def delete_old_firmwares(self,pattern):
                for file in glob.glob(pattern):
                    try:
                        os.remove(file)
                        logger.info(f"删除旧固件: {file}")
                    except Exception as e:
                        logger.warning(f"删除文件失败: {file}，错误: {e}")



    def test_exception(self, case_config):


        self.delete_old_firmwares("./case/xuitra/boot/release/STM32_Compressed_Motor_Firmware_*")
        self.delete_old_firmwares("./case/xuitra/boot/release/ESP32_Masterboard_Firmware_*")
        self.delete_old_firmwares("./case/xuitra/boot/baase/STM32_Compressed_Motor_Firmware_*")
        self.delete_old_firmwares("./case/xuitra/boot/base/ESP32_Masterboard_Firmware_*")
        #示例使用

        url = "http://8.217.150.31:8090/webDevice/downloadFirmwareTest?type=1&firmwareType=1&randomString=Hypershell2024&index=0"
        save_path = os.path.join(save_base_dir, "release")  # 请修改为你希望保存文件的路径
        self.download_firmware(url, save_path)

        url = "http://8.217.150.31:8090/webDevice/downloadFirmwareTest?type=1&firmwareType=1&randomString=Hypershell2024&index=1"
        save_path = os.path.join(save_base_dir, "base")  # 请修改为你希望保存文件的路径
        self.download_firmware(url, save_path)


        #电机固件

        url = "http://8.217.150.31:8090/webDevice/downloadFirmwareTest?type=1&firmwareType=3&randomString=Hypershell2024&index=0"
        save_path = os.path.join(save_base_dir, "release")  # 请修改为你希望保存文件的路径
        self.download_firmware(url, save_path)

        url = "http://8.217.150.31:8090/webDevice/downloadFirmwareTest?type=1&firmwareType=3&randomString=Hypershell2024&index=1"
        save_path = os.path.join(save_base_dir, "base")  # 请修改为你希望保存文件的路径
        self.download_firmware(url, save_path)

