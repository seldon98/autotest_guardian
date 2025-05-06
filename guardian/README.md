# guradian auto test framework 

文件目录结构以及内容含义

case       用于存放产品测试用例， 目录下有两级目录，case/A/B  A作为产品目录，B作为模块目录

common     用于存放公共类，目录下有一级目录，plan/A  A作为产品目录

plan       用于存放测试计划内容及基础产品配置信息，如：串口、设备号

logs       用于存放测试日志

temps      用于存放测试执行完成后生成json文件

reports    用于测试完成后，通过allure生成测试报告


run.py     作为框架调研的主函数， 可通过传入参数，调用指定的测试计划 ， 如 python.exe run.py -P wm630 -M smoke, 调用plan/wm630/somke.yaml 配置好的测试计划

-P 代指项目代号   -M 代指测试计划名

conftest.py 于定义全局共享的测试配置、复用的前置条件（如数据库连接、浏览器初始化）和清理逻辑

pytest.in 用于定义项目级默认行为和参数

plan/A/device.yaml ,用于记录产品基础设备信息、端口号，格式结构固定，如：

product: 'wm630'
serial_port: COM11
baud_rate: 9600
parity: N
data_bits: 8
stop_bits: 1

plan/A/测试计划.yaml ， 用于记录测试计划顺序及描述，格式结构固定，如：

test_cases:
  - name: test_case_1  # 测试文件名， 测试文件均以test_开头
    loops: 1   # 设置用例循环测试
    module: reboot  # 测试文件上一级目录名
    description: "This is a test case for TestCase1"
    product: wm630   # 产品代号

  - name: test_case_2
    loops: 1
    module: reboot
    description: "This is a test case for TestCase2"
    product: wm630

  - name: test_case_3
    loops: 1
    module: reboot
    description: "This is a test case for TestCase3"
    product: wm630


