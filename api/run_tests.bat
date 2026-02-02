@echo off
REM Integration Test Runner Script for Windows
REM Runs the AURELIUS API integration test suite

setlocal enabledelayedexpansion

echo ================================
echo AURELIUS Integration Test Suite
echo ================================
echo.

REM Check if API is running
echo Checking API connectivity...
for /f %%A in ('curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/health 2^>nul') do set HTTP_CODE=%%A

if "%HTTP_CODE%"=="" set HTTP_CODE=000
if not "%HTTP_CODE%"=="200" (
    echo ❌ API server is not running on http://127.0.0.1:8000
    echo.
    echo Start the API with:
    echo   cd api
    echo   python -m uvicorn main:app --reload
    exit /b 1
)

echo ✅ API server is running
echo.

REM Run Python test suite
echo Running integration tests...
python test_integration.py

echo.
echo Integration tests complete!
