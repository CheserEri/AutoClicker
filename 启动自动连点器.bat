@echo off
chcp 65001 >nul
title 自动连点器 - 环境检测与启动

echo.
echo ========================================
echo    自动连点器 - 环境检测与自动修复
echo ========================================
echo.

setlocal enabledelayedexpansion

:: 检测管理员权限（安装运行时需要）
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [提示] 需要管理员权限来安装运行时组件
    echo        正在请求提升权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: ============================================
:: 检测1: 系统架构
:: ============================================
echo [1/3] 检测系统架构...
if exist "%ProgramFiles(x86)%" (
    echo       [通过] 64位系统
) else (
    echo       [失败] 32位系统 - 不兼容
    echo       本程序仅支持64位Windows系统
    pause
    exit /b 1
)
echo.

:: ============================================
:: 检测2: Windows版本
:: ============================================
echo [2/3] 检测Windows版本...
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo       当前版本: Windows !VERSION!

for /f "tokens=1 delims=." %%a in ("!VERSION!") do set WIN_MAJOR=%%a

if !WIN_MAJOR! geq 10 (
    echo       [Win10+] 使用 Win10 专用版本
    set "EXE_NAME=AutoClicker-Win10.exe"
    set "NEED_VCR=0"
) else (
    echo       [Win7/8] 使用 Win7 兼容版本
    set "EXE_NAME=AutoClicker-Win7.exe"
    set "NEED_VCR=1"
)
echo.

:: ============================================
:: 检测3: VC++运行时
:: ============================================
echo [3/3] 检测运行时环境...

set "VC_FOUND=0"
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Major >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=3" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Major 2^>nul ^| findstr Major') do set VC_MAJOR=%%a
    if defined VC_MAJOR (
        if !VC_MAJOR! geq 14 set "VC_FOUND=1"
    )
)

if !VC_FOUND! equ 1 (
    echo       [通过] VC++运行时已安装
    goto :LAUNCH
)

echo       [缺失] VC++运行时未安装

if "!NEED_VCR!"=="0" (
    echo       Win10+系统可能已内置，尝试启动...
    goto :LAUNCH
)

echo.
echo       Win7/8系统需要安装VC++运行时才能运行。
echo       即将自动下载安装（一次性操作）...
echo.

set /p "CONFIRM=是否继续安装？(Y/N，默认Y): "
if /i "!CONFIRM!"=="N" (
    echo 已取消，程序可能无法正常运行。
    pause
    exit /b
)

echo.
echo 正在下载 Visual C++ Redistributable...
echo 请稍候...

set "VC_URL=https://aka.ms/vs/17/release/vc_redist.x64.exe"
set "VC_FILE=%TEMP%\vc_redist.x64.exe"

powershell -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "$ProgressPreference = 'SilentlyContinue'; " ^
    "try { " ^
    "    Invoke-WebRequest -Uri '%VC_URL%' -OutFile '%VC_FILE%' -UseBasicParsing; " ^
    "    Write-Host '下载完成'; " ^
    "} catch { " ^
    "    Write-Host '下载失败: ' + $_.Exception.Message; " ^
    "    exit 1; " ^
    "}"

if not exist "%VC_FILE%" (
    echo.
    echo [错误] 下载失败！
    echo 请手动下载安装: %VC_URL%
    pause
    exit /b 1
)

echo 正在安装VC++运行时（可能需要1-3分钟）...
"%VC_FILE%" /install /quiet /norestart
set "INSTALL_RC=%errorlevel%"
del "%VC_FILE%" >nul 2>&1

if %INSTALL_RC% equ 0 (
    echo [成功] VC++运行时安装完成
) else if %INSTALL_RC% equ 3010 (
    echo [成功] 安装完成，需重启计算机后重新运行本程序
    pause
    exit /b
) else if %INSTALL_RC% equ 1641 (
    echo [成功] 安装完成，需重启计算机后重新运行本程序
    pause
    exit /b
) else (
    echo [警告] 安装可能未成功（错误码: %INSTALL_RC%）
    echo 请手动下载: %VC_URL%
    pause
    exit /b 1
)

echo.

:LAUNCH
echo ========================================
echo    启动程序: %EXE_NAME%
echo ========================================
echo.
echo 按任意键启动自动连点器...
pause >nul

if exist "%~dp0%EXE_NAME%" (
    start "" "%~dp0%EXE_NAME%"
) else (
    echo [错误] 未找到 %EXE_NAME%
    echo 请确保本脚本与程序文件在同一目录。
    pause
)
