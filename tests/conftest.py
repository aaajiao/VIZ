"""
Pytest 配置和共享 fixtures

提供测试中常用的 fixtures，包括临时目录、随机数生成器等。
"""

import os
import sys
import random
import tempfile
import pytest

# 确保项目根目录在 path 中
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)


@pytest.fixture
def rng():
    """提供固定种子的随机数生成器"""
    return random.Random(42)


@pytest.fixture
def temp_dir():
    """提供临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def project_root():
    """项目根目录"""
    return _project_root
