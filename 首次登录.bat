@echo off
chcp 65001 >nul
title mail.com 首次登录设置
cd /d "%~dp0"
python login_once.py
pause
