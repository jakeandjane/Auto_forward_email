@echo off
chcp 65001 >nul
title 安装依赖
cd /d "%~dp0"
echo ============================================
echo  正在安装 Python 依赖...
echo ============================================
echo.
pip install -r requirements.txt
echo.
echo ============================================
echo  正在下载 Playwright 浏览器(约 150MB)...
echo ============================================
@REM echo.
@REM python -m playwright install chromium
echo.
echo ============================================
echo  ✅ 安装完成!
echo ============================================
pause
