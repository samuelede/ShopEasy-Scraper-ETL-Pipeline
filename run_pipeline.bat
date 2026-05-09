@echo off
:: =============================================================================
:: run_pipeline.bat
:: Runs the Books Price Intelligence ETL pipeline
:: Schedule this file using Windows Task Scheduler for automated runs
:: =============================================================================

:: Move to the project root folder (where this .bat file lives)
cd /d "%~dp0"

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Log the start time
echo [%date% %time%] Pipeline starting... >> data\logs\scheduler.log

:: Run the pipeline
python python\pipeline.py

:: Log whether it succeeded or failed
if %ERRORLEVEL% == 0 (
    echo [%date% %time%] Pipeline completed successfully. >> data\logs\scheduler.log
) else (
    echo [%date% %time%] Pipeline FAILED with error code %ERRORLEVEL%. >> data\logs\scheduler.log
)

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat