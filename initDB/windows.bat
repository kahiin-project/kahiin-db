@echo off
setlocal EnableDelayedExpansion

if "%~10"=="" (
    echo Usage: %0 <db_name> <db_user> <db_password> <db_host> <email> <email_password> <smtp_server> <smtp_port> <encryption_key> <root_password>
    exit /b 1
)

set db_name=%~1
set db_user=%~2
set db_password=%~3
set db_host=%~4
set email=%~5
set email_password=%~6
set smtp_server=%~7
set smtp_port=%~8
set encryption_key=%~9
set root_password=%~10

if "!db_host!"=="" set db_host=localhost
if "!smtp_port!"=="" set smtp_port=587

if "!encryption_key:~15!"=="" (
    echo La clé de chiffrement doit contenir au moins 16 caractères.
    exit /b 1
)

where mysql >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo MySQL n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer MySQL et réessayer.
    exit /b 1
)

echo Initialisation de la base de données Kahiin pour Windows...

mysql -u root -p"%root_password%" -e "CREATE DATABASE IF NOT EXISTS !db_name!;" >nul 2>&1
mysql -u root -p"%root_password%" -e "CREATE USER '!db_user!'@'!db_host!' IDENTIFIED BY '!db_password!';" >nul 2>&1
mysql -u root -p"%root_password%" -e "GRANT ALL PRIVILEGES ON !db_name!.* TO '!db_user!'@'!db_host!';" >nul 2>&1
mysql -u root -p"%root_password%" -e "FLUSH PRIVILEGES;" >nul 2>&1

python config-maker.py "!db_password!" "!db_host!" "!db_user!" "!db_name!" "!email!" "!email_password!" "!smtp_server!" "!smtp_port!" "!encryption_key!" >nul 2>&1

echo Configuration complete!

exit /b 0