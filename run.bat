@echo off
chcp 65001 >nul
title Instagram Downloader (Zero-Setup)

echo ==============================================
echo       Instagram Downloader (Zero-Setup)
echo ==============================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не установлен или не добавлен в PATH!
    echo Пожалуйста, скачайте и установите Python с официального сайта: https://www.python.org/downloads/
    echo При установке обязательно поставьте галочку "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: Запуск основного скрипта, передача всех аргументов
if "%~1"=="" (
    :: Запуск без аргументов - скрипт сам запросит ссылку
    python ig_downloader.py
) else (
    :: Запуск с аргументами (CLI режим)
    python ig_downloader.py %*
)

echo.
pause
