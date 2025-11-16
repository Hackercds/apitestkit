"""
配置管理模块

提供全局配置管理功能，包括基础配置定义、项目路径管理、外部配置文件加载与合并等。
支持JSON/YAML格式、环境变量替换、分层配置和配置验证。
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

# 设置模块日志
logger = logging.getLogger(__name__)

# 尝试导入YAML支持，若未安装则提供提示
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigManager:
    """
    配置管理器类，负责管理框架的所有配置项
    支持JSON/YAML配置文件、环境变量替换、分层配置和配置验证
    """
    
    # 环境变量替换模式
    ENV_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(self):
        # 基础配置
        self._config = {
            'log_level': 'INFO',
            'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'default_timeout': 30,
            'base_url': '',
            'headers': {},
            'verify_ssl': True,
            'proxy': None,
            # AI/Agent相关配置
            'ai': {
                'default_model': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 1000,
                'timeout': 60,
            },
            # 流式响应配置
            'streaming': {
                'chunk_size': 1024,
                'default_format': 'json',
                'max_buffer_size': 10 * 1024 * 1024,  # 10MB
            },
            # 重试配置
            'retry': {
                'enabled': True,
                'max_retries': 3,
                'backoff_factor': 0.3,
                'status_codes': [500, 502, 503, 504],
            },
            # 并发配置
            'concurrency': {
                'max_workers': 10,
                'timeout': 300,
            },
        }
        
        # 配置验证规则
        self._validation_rules = {
            'log_level': lambda x: x in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'default_timeout': lambda x: isinstance(x, int) and x > 0,
            'verify_ssl': lambda x: isinstance(x, bool),
            'ai.temperature': lambda x: isinstance(x, (int, float)) and 0 <= x <= 2,
            'ai.max_tokens': lambda x: isinstance(x, int) and x > 0,
        }
        
        # 项目路径配置
        self._setup_paths()
    
    def _setup_paths(self):
        """
        设置项目相关路径
        使用Path对象确保跨平台兼容性
        """
        # 获取当前工作目录
        working_dir = Path.cwd()
        self._config['working_dir'] = str(working_dir)
        
        # 配置目录
        config_dir = working_dir / 'config'
        self._config['config_dir'] = str(config_dir)
        
        # 日志目录
        log_dir = working_dir / 'logs'
        self._config['log_dir'] = str(log_dir)
        
        # 报告目录
        report_dir = working_dir / 'reports'
        self._config['report_dir'] = str(report_dir)
        
        # 数据目录
        data_dir = working_dir / 'data'
        self._config['data_dir'] = str(data_dir)
        
        # Agent模板目录
        agent_templates_dir = config_dir / 'agent_templates'
        self._config['agent_templates_dir'] = str(agent_templates_dir)
        
        # 创建必要的目录
        dirs_to_create = [config_dir, log_dir, report_dir, data_dir, agent_templates_dir]
        for dir_path in dirs_to_create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"确保目录存在: {dir_path}")
            except Exception as e:
                logger.error(f"创建目录失败 {dir_path}: {e}")
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """
        递归解析配置中的环境变量
        
        Args:
            config: 配置值（可能是字典、列表或基本类型）
            
        Returns:
            解析环境变量后的值
        """
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str):
            # 替换${ENV_VAR}格式的环境变量
            def replace_env_var(match):
                env_var = match.group(1)
                return os.environ.get(env_var, match.group(0))
            result = self.ENV_PATTERN.sub(replace_env_var, config)
            # 尝试类型转换
            return self._try_convert_type(result)
        return config
    
    def _try_convert_type(self, value: str) -> Union[str, int, float, bool]:
        """
        尝试将字符串值转换为合适的类型
        
        Args:
            value: 字符串值
            
        Returns:
            转换后的值
        """
        # 处理布尔值
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        
        # 处理整数
        if value.isdigit():
            try:
                return int(value)
            except ValueError:
                pass
        
        # 处理浮点数
        if '.' in value:
            try:
                # 确保所有部分都是数字
                parts = value.split('.')
                if all(part.isdigit() for part in parts if part):
                    return float(value)
            except ValueError:
                pass
        
        # 默认返回字符串
        return value
    
    def _load_config_file(self, config_file: str) -> Optional[Dict[str, Any]]:
        """
        从配置文件加载配置数据
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            配置字典，加载失败返回None
        """
        # 使用Path对象确保跨平台兼容性
        config_path = Path(config_file)
        if not config_path.exists():
            logger.debug(f"配置文件不存在: {config_file}")
            return None
        
        try:
            with config_path.open('r', encoding='utf-8') as f:
                # 根据文件扩展名选择解析器
                if config_path.suffix in ('.yaml', '.yml'):
                    if not YAML_AVAILABLE:
                        logger.warning("尝试加载YAML配置文件，但未安装PyYAML。请安装: pip install pyyaml")
                        return None
                    config_data = yaml.safe_load(f)
                else:
                    # 默认使用JSON格式
                    config_data = json.load(f)
                
                # 解析环境变量
                logger.debug(f"成功加载配置文件: {config_file}")
                return self._resolve_env_vars(config_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON格式错误 {config_file}: {e}")
            return None
        except yaml.YAMLError as e:
            logger.error(f"YAML格式错误 {config_file}: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"编码错误 {config_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_file}: {e}")
            return None
    
    def load_config(self, config_file: str) -> bool:
        """
        从配置文件加载配置
        支持JSON和YAML格式
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            是否加载成功
        """
        config_data = self._load_config_file(config_file)
        if config_data:
            # 使用update方法进行深度合并，而不是简单的update
            self.update(config_data)
            logger.info(f"成功从 {config_file} 加载配置")
            return True
        return False
    
    def load_configs(self, config_files: list) -> bool:
        """
        加载多个配置文件，后面的文件会覆盖前面的配置
        
        Args:
            config_files: 配置文件路径列表
            
        Returns:
            是否至少成功加载了一个配置文件
        """
        success = False
        for config_file in config_files:
            if self.load_config(config_file):
                success = True
        return success
    
    def load_default_configs(self):
        """
        加载默认配置文件链
        按以下顺序加载：
        1. config/default.json (或 .yaml)
        2. config/{环境}.json (或 .yaml)
        3. config/local.json (或 .yaml)
        """
        config_dir = self._config['config_dir']
        env = os.environ.get('API_TEST_ENV', 'development')
        
        config_files = []
        
        # 检查各种格式的默认配置文件
        for base_name in ['default', env, 'local']:
            for ext in ['.json', '.yaml', '.yml']:
                file_path = Path(config_dir) / f'{base_name}{ext}'
                if file_path.exists():
                    config_files.append(file_path)
                    break
        
        return self.load_configs(config_files)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，可以使用点分隔符访问嵌套配置
            default: 默认值，当配置不存在时返回
            
        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，可以使用点分隔符访问嵌套配置
            value: 要设置的值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """
        批量更新配置，支持深度合并
        
        Args:
            config_dict: 配置字典
        """
        def deep_merge(target: Dict[str, Any], source: Dict[str, Any]):
            """深度合并两个字典"""
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    # 递归合并嵌套字典
                    deep_merge(target[key], value)
                else:
                    # 对于非字典类型或新键，直接覆盖/添加
                    target[key] = value
            return target
        
        try:
            deep_merge(self._config, config_dict)
            logger.debug(f"配置已更新，验证配置有效性")
            return self.validate_config()
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            raise
    
    def validate_config(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            配置是否有效
        """
        is_valid = True
        for key, validator in self._validation_rules.items():
            value = self.get(key)
            if value is not None and not validator(value):
                logger.warning(f"配置项 '{key}' 的值 '{value}' 无效")
                is_valid = False
        
        # 额外验证路径配置
        for path_key in ['working_dir', 'config_dir', 'log_dir', 'report_dir', 'data_dir']:
            path_value = self.get(path_key)
            if path_value:
                path_obj = Path(path_value)
                if not path_obj.exists():
                    logger.warning(f"配置路径不存在: {path_key} = {path_value}")
                    # 尝试创建目录
                    try:
                        path_obj.mkdir(exist_ok=True, parents=True)
                        logger.info(f"已自动创建缺失的目录: {path_value}")
                    except Exception as e:
                        logger.error(f"无法创建目录 {path_value}: {e}")
                        is_valid = False
        
        return is_valid
    
    def save_config(self, config_file: str) -> bool:
        """
        保存配置到文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            是否保存成功
        """
        try:
            # 使用Path对象确保跨平台兼容性
            config_path = Path(config_file)
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with config_path.open('w', encoding='utf-8') as f:
                if config_path.suffix in ('.yaml', '.yml'):
                    if not YAML_AVAILABLE:
                        logger.warning("尝试保存YAML配置文件，但未安装PyYAML。将保存为JSON格式。")
                        json.dump(self._config, f, indent=2, ensure_ascii=False)
                    else:
                        yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"配置已保存到: {config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_ai_config(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        获取AI/Agent相关配置
        
        Args:
            model: 模型名称，如果指定，会尝试获取该模型的特定配置
            
        Returns:
            AI配置字典
        """
        ai_config = self.get('ai', {}).copy()
        if model and 'models' in ai_config and model in ai_config['models']:
            # 合并特定模型的配置
            model_config = ai_config['models'][model]
            ai_config.update(model_config)
        return ai_config
    
    def get_streaming_config(self) -> Dict[str, Any]:
        """
        获取流式响应相关配置
        
        Returns:
            流式响应配置字典
        """
        return self.get('streaming', {}).copy()
    
    def get_all(self):
        """
        获取所有配置
        
        Returns:
            所有配置的字典
        """
        return self._config.copy()
    
    def set_output_dir(self, output_dir: str):
        """
        设置输出目录（日志、报告等）
        
        Args:
            output_dir: 输出目录路径
        """
        try:
            # 使用Path对象确保跨平台兼容性
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            self._config['output_dir'] = str(output_path)
            
            # 设置子目录
            log_dir = output_path / 'logs'
            report_dir = output_path / 'reports'
            
            self._config['log_dir'] = str(log_dir)
            self._config['report_dir'] = str(report_dir)
            
            # 创建子目录
            log_dir.mkdir(parents=True, exist_ok=True)
            report_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"输出目录已设置为: {output_dir}")
        except Exception as e:
            logger.error(f"设置输出目录失败 {output_dir}: {e}")
            raise
    
    def set_input_dir(self, input_dir: str):
        """
        设置输入目录
        
        Args:
            input_dir: 输入目录路径
        """
        try:
            # 使用Path对象确保跨平台兼容性
            input_path = Path(input_dir)
            input_path.mkdir(parents=True, exist_ok=True)
            
            self._config['input_dir'] = str(input_path)
            logger.info(f"输入目录已设置为: {input_dir}")
        except Exception as e:
            logger.error(f"设置输入目录失败 {input_dir}: {e}")
            raise
    
    def from_environment(self, prefix: str = 'API_TEST_'):
        """
        从环境变量加载配置
        
        Args:
            prefix: 环境变量前缀
        """
        loaded_count = 0
        for key, value in os.environ.items():
            if key.startswith(prefix):
                try:
                    # 移除前缀并转换为小写
                    config_key = key[len(prefix):].lower()
                    
                    # 使用统一的类型转换方法
                    converted_value = self._try_convert_type(value)
                    
                    # 支持下划线分隔的嵌套键，转换为点号分隔
                    config_key = config_key.replace('_', '.')
                    self.set(config_key, converted_value)
                    loaded_count += 1
                    logger.debug(f"从环境变量加载配置: {key} -> {config_key} = {converted_value}")
                except Exception as e:
                    logger.error(f"处理环境变量 {key} 失败: {e}")
        
        if loaded_count > 0:
            logger.info(f"从环境变量成功加载 {loaded_count} 个配置项")
            self.validate_config()
        return loaded_count
    
    # 向后兼容性方法
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（向后兼容方法）
        """
        return self.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """
        设置配置值（向后兼容方法）
        """
        self.set(key, value)
    
    def load_config_file(self, config_file: str) -> bool:
        """
        加载配置文件（向后兼容方法）
        """
        return self.load_config(config_file)
    
    def merge_configs(self, config_dict: Dict[str, Any]):
        """
        合并配置字典（向后兼容方法）
        """
        self.update(config_dict)
    
    def merge_config(self, config_dict: Dict[str, Any]):
        """
        合并配置字典（向后兼容方法）
        """
        self.update(config_dict)


# 创建全局配置管理器实例
config_manager = ConfigManager()