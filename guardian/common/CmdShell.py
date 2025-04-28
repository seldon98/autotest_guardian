
import subprocess
import platform


class CommandExecutor:
    def __init__(self):
        self.encoding = 'gbk' if platform.system() == 'Windows' else 'utf-8'

    def cmd_shell(self, command):
        """执行命令并返回 (状态, 输出) 二元组"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding=self.encoding
            )
            return (True, result.stdout)  # 明确返回元组
        except subprocess.CalledProcessError as e:
            return (False, e.stderr)  # 确保始终返回两个值
        except Exception as e:
            return (False, str(e))  # 捕获其他异常