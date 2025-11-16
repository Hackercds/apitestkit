# 安装指南

本文档详细说明如何安装和配置ApiTestKit框架。

## 前提条件

在安装ApiTestKit之前，请确保您的系统满足以下要求：

- Python 3.7 或更高版本
- pip 20.0 或更高版本

### 检查Python版本

可以通过以下命令检查您的Python版本：

```bash
python --version
# 或
python3 --version
```

确保输出显示Python 3.7或更高版本。

## 安装方法

### 方法1：通过PyPI安装（推荐）

最简单的安装方式是通过pip直接从PyPI安装：

```bash
pip install apitestkit
```

如果需要安装特定版本：

```bash
pip install apitestkit==1.0.0
```

### 方法2：从源码安装

如果您需要最新的开发版本，可以从源码安装：

1. 克隆代码库：

```bash
git clone https://github.com/Hackercd/apitestkit.git
cd apitestkit
```

2. 安装开发版本：

```bash
pip install -e .
```

### 方法3：安装wheel包

如果您已经有了wheel文件，可以直接安装：

```bash
pip install apitestkit-1.0.0-py3-none-any.whl
```

## 安装开发依赖

如果您想要参与开发或运行测试，可以安装开发依赖：

```bash
pip install -e "[dev]"
```

或者手动安装依赖：

```bash
pip install -r requirements.txt
```

## 验证安装

安装完成后，您可以通过以下方式验证安装是否成功：

```bash
python -c "import apitestkit; print(apitestkit.__version__)"
```

如果输出显示版本号（如`1.0.0`），则表示安装成功。

## 升级框架

要升级到最新版本，可以使用：

```bash
pip install --upgrade apitestkit
```

## 卸载框架

如果需要卸载框架，可以使用：

```bash
pip uninstall apitestkit
```

## 常见问题

### 依赖冲突

如果遇到依赖冲突问题，可以尝试使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 激活虚拟环境（Linux/MacOS）
source venv/bin/activate

# 然后安装框架
pip install apitestkit
```

### 权限问题

在某些系统上，可能需要管理员权限进行安装：

```bash
# Windows以管理员身份运行命令提示符
pip install apitestkit

# Linux/MacOS使用sudo
sudo pip install apitestkit
```

### 安装超时

如果遇到网络问题导致安装超时，可以使用国内镜像源：

```bash
# 使用清华大学镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple apitestkit

# 使用阿里云镜像源
pip install -i https://mirrors.aliyun.com/pypi/simple/ apitestkit
```

## 下一步

安装完成后，您可以参考[配置指南](configuration_guide.md)进行框架配置，或者查看[快速开始指南](quick_start.md)了解如何使用框架。