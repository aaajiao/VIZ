#!/bin/bash
# VIZ Development Environment Setup
# 开发环境依赖安装脚本

set -e

echo "Installing development dependencies..."

# FFmpeg - for MP4 video output
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing FFmpeg..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    elif command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "Warning: Could not install FFmpeg (no apt-get or brew found)"
    fi
else
    echo "FFmpeg already installed"
fi

# Pyright - Python type checker
if ! command -v pyright &> /dev/null; then
    echo "Installing Pyright..."
    if command -v npm &> /dev/null; then
        npm install -g pyright
    elif command -v pip &> /dev/null; then
        pip install pyright
    else
        echo "Warning: Could not install Pyright (no npm or pip found)"
    fi
else
    echo "Pyright already installed"
fi

# Python dependencies
if command -v pip &> /dev/null; then
    echo "Installing Python dependencies..."
    pip install Pillow>=9.0.0
fi

echo "Development environment setup complete!"
