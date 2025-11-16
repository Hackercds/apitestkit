"""
apitestkit包的安装配置文件
"""

from setuptools import setup, find_packages
import os
import re

# 从__init__.py文件中获取版本信息
def get_version():
    """从__init__.py文件中提取版本号"""
    with open(os.path.join('apitestkit', '__init__.py'), 'r', encoding='utf-8') as f:
        content = f.read()
        version_match = re.search(r'__version__ = ["\']([^"]*)["\']', content)
        if version_match:
            return version_match.group(1)
        return "1.0.0"  # 默认版本号

# 读取README文件内容作为长描述
def get_long_description():
    """读取README.md文件内容作为长描述"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "apitestkit - 一个轻量级的API测试框架"

version = get_version()
long_description = get_long_description()

setup(
    # 包的基本信息
    name="apitestkit",
    version=version,
    description="一个轻量级、高性能的API自动化测试框架",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Hackercd",
    author_email="Hackercd@foxmail.com",
    url="https://github.com/Hackercd/apitestkit",
    license="MIT",
    
    # 包的分类信息
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Testers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # 关键词
    keywords=[
        "api", "testing", "automation", "rest", "http", "test-framework",
        "api-testing", "automated-testing", "qa", "quality-assurance"
    ],
    
    # 查找包
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    # 最小化依赖项
    install_requires=[
        "requests>=2.25.0",  # HTTP请求库
        "rich>=10.0.0",  # 终端美化输出
        "matplotlib>=3.4.0",  # 图表生成
        "pandas>=1.3.0",  # 数据处理和CSV/Excel导出
        "jinja2>=3.0.0",  # HTML模板渲染
        "pyyaml>=6.0",  # YAML配置文件支持
        "jsonschema>=3.2.0",  # JSON Schema验证
    ],
    # 可选依赖项
    extras_require={
        "dev": [
            "pytest>=6.0.0",  # 测试框架
            "jsonschema>=3.2.0",  # JSON Schema验证
            "wheel>=0.36.0",  # 构建wheel包
            "twine>=3.4.0",  # 上传包到PyPI
            "flake8>=3.9.0",  # 代码风格检查
        ],
        "schema": [
            "jsonschema>=3.2.0",  # JSON Schema验证
        ],
    },
    # 数据文件
    package_data={
        "apitestkit": ["py.typed"],  # 类型提示文件
    },
    
    # 包含非代码文件
    include_package_data=True,
    
    # 入口点（命令行工具）- 目前暂未实现
    entry_points={},

    # 项目URL
    project_urls={
        "Documentation": "https://github.com/Hackercd/apitestkit/README.md",
        "Source": "https://github.com/Hackercd/apitestkit",
        "Tracker": "https://github.com/Hackercd/apitestkit/issues",
    },
    
    # Python版本要求
    python_requires=">=3.7,<4.0",
    
    # 提供详细的安装信息
    zip_safe=False,
    platforms="any",
)