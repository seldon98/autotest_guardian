[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Webhook 地址
$webhookUrl = "https://open.feishu.cn/open-apis/bot/v2/hook/3d50eb4e-1db3-4e58-9b92-9d5c77fa9528"

# Jenkins 环境变量
$jobName = $env:JOB_NAME
$buildNumber = $env:BUILD_NUMBER
$buildUrl = $env:BUILD_URL
$timestamp = $env:TIMESTAMP
$reportPath = "file://E:/Jenkins/SWS_Git/autotest_guardian/guardian/reports/$timestamp/index.html"

# 构造消息内容
$message = @{
    msg_type = "post"
    content  = @{
        post = @{
            zh_cn = @{
                title = "✅ Jenkins 通知"
                content = @(
                    @(
                        @{ tag = "text"; text = "🏷️ 任务名称：" },
                        @{ tag = "text"; text = $jobName }
                    ),
                    @(
                        @{ tag = "text"; text = "🔢 构建编号：" },
                        @{ tag = "text"; text = "#$buildNumber" }
                    ),
                    @(
                        @{ tag = "text"; text = "📄 测试报告：" },
                        @{ tag = "a"; text = "查看报告"; href = $reportPath }
                    ),
                    @(
                        @{ tag = "text"; text = "🔗 构建详情：" },
                        @{ tag = "a"; text = "查看详情"; href = $buildUrl }
                    )
                )
            }
        }
    }
}

# 转换为 JSON
$jsonBody = $message | ConvertTo-Json -Depth 10 -Compress

# 可选：调试输出 JSON 内容
Write-Output $jsonBody

# 发送请求
Invoke-RestMethod -Uri $webhookUrl -Method Post -Body $jsonBody -ContentType 'application/json'
