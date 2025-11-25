@echo off
echo 启动微信公众号机器人服务...
echo.
echo 请确保已配置微信公众号Token
echo 服务器URL配置为: http://your-domain.com/wechat
echo.

cd /d "f:\work\FutureSample\FutureSample\cloud"
python wechat_bot.py

pause