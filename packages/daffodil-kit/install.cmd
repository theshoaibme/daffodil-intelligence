@echo off
REM CopyCat Kit — Windows CMD one-liner (same install.py, auto-detects OS)
REM   curl -fsSL https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/packages/daffodil-kit/install.cmd

powershell -NoProfile -ExecutionPolicy Bypass -Command "irm '%~dp0install.ps1' | iex" 2>nul || (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
)
