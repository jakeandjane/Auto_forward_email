@echo off
chcp 65001 >nul
title mail.com 自动转发机器人
cd /d "%~dp0"
echo ============================================
echo  mail.com 自动转发机器人
echo ============================================
echo.
echo 启动中...按 Ctrl+C 可以停止
echo.
python forward_bot.py
echo.
echo 程序已退出,按任意键关闭窗口...
pause >nul
