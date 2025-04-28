@echo off
call .venv\Scripts\activate

echo 清理历史报告数据...
if exist temps rmdir /s /q temps
if exist reports rmdir /s /q reports

echo 运行测试用例...
pytest || echo 测试运行完成（忽略失败）

echo 生成Allure报告...
allure generate temps -o reports --clean

echo 打开报告...
start "" "reports\index.html"
