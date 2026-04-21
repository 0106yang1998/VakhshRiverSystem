# Project Run Guide

This project is configured to run with the conda environment:

`E:\anaconda\envs\VakhshRiverSystem`

## Quick Start

Double-click:

`run_app.bat`

Or run in PowerShell:

```powershell
.\run_app.ps1
```

## PyCharm

Use the shared run configuration:

`Run VakhshRiverSystem`

It runs:

- script: `main.py`
- working directory: project root
- environment variables:
  - `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu --disable-gpu-compositing`
  - `QT_OPENGL=software`

## Optional

To run in offscreen mode for checks:

```powershell
.\run_app.ps1 -QtPlatform offscreen
```
