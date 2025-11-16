# apitestkit 安装指南

本文档提供了 apitestkit 的详细安装步骤，帮助您快速搭建 API 测试环境。

## 系统要求

- **操作系统**: Windows 7 及以上 / macOS 10.12 及以上 / Linux (Ubuntu 16.04+, CentOS 7+)
- **Python 版本**: Python 3.7+ (推荐 Python 3.8 或更高版本)
- **pip 版本**: pip 19.0 及以上

## 安装方法

### 方法一：使用 pip 安装（推荐）

最简单的安装方式是通过 pip 包管理器安装：

```bash
pip install apitestkit
```

如果您想安装特定版本的 apitestkit：

```bash
pip install apitestkit==1.0.0  # 替换为您需要的版本号
```

### 方法二：从源码安装

如果您需要最新的开发版本或希望修改源码，可以从源码安装：

1. 克隆代码仓库：

```bash
git clone https://github.com/yourusername/apitestkit.git
cd apitestkit
```

2. 安装依赖项：

```bash
pip install -r requirements.txt
```

3. 安装 apitestkit（开发模式）：

```bash
pip install -e .
```

或者直接安装：

```bash
python setup.py install
```

## 验证安装

安装完成后，您可以通过以下命令验证 apitestkit 是否已正确安装：

```bash
python -c "import apitestkit; print(f'apitestkit 版本: {apitestkit.__version__}')"
```

如果命令执行成功并显示版本信息，则表示安装成功。

## 安装依赖项

apitestkit 的主要依赖项会在安装过程中自动安装，但如果您需要手动安装，可以参考以下列表：

### 核心依赖

- **requests**: 用于发送 HTTP 请求
- **pyyaml**: 用于解析 YAML 配置文件
- **jinja2**: 用于模板渲染
- **markupsafe**: 用于安全的字符串处理
- **python-dateutil**: 用于日期时间处理
- **tabulate**: 用于表格输出

### 报告生成依赖

- **jinja2**: 用于 HTML 报告生成
- **openpyxl**: 用于 Excel 报告生成
- **pandas**: 用于数据处理和 CSV 报告生成
- **matplotlib**: 用于图表生成（可选）

### 高级功能依赖

- **pytest**: 用于与 pytest 集成（可选）
- **allure-pytest**: 用于 Allure 报告集成（可选）

## 升级 apitestkit

要升级已安装的 apitestkit 到最新版本，可以使用以下命令：

```bash
pip install --upgrade apitestkit
```

## 卸载 apitestkit

如果您需要卸载 apitestkit，可以使用以下命令：

```bash
pip uninstall apitestkit
```

## 常见安装问题

### 问题 1：权限错误

在某些系统上，您可能会遇到权限错误。您可以尝试使用管理员权限安装或使用用户目录安装：

```bash
pip install --user apitestkit
```

### 问题 2：依赖项冲突

如果您的环境中存在依赖项冲突，可以考虑使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv apitestkit_env

# 激活虚拟环境
# Windows:
apitestkit_env\Scripts\activate
# macOS/Linux:
source apitestkit_env/bin/activate

# 在虚拟环境中安装
pip install apitestkit
```

### 问题 3：Python 版本不兼容

确保您使用的是 Python 3.7 或更高版本：

```bash
python --version
```

如果您的系统中安装了多个 Python 版本，可以明确指定使用 Python 3：

```bash
python3 -m pip install apitestkit
```

## 获取帮助

如果您在安装过程中遇到任何问题，请参考以下资源：

- 查看项目的 [GitHub Issues](https://github.com/Hackercd/apitestkit/issues) 页面
- 检查详细的错误信息并尝试在搜索引擎中查找解决方案
- 如果您确定这是一个新问题，请考虑在 GitHub 上提交一个新的 issue

祝您使用愉快！