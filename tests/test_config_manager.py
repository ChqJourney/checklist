from src.config.config_manager import ConfigManager


def test_config_init():
    config_manager = ConfigManager()
    assert config_manager is not None

def test_system_config_is_not_none():
    cfg_manager = ConfigManager()
    system_config = cfg_manager.get_system_config()
    assert system_config is not None

def test_user_config_is_not_none():
    cfg_manager = ConfigManager()
    user_config = cfg_manager.get_user_config()
    assert user_config is not None

def test_base_dir_is_valid():
    cfg_manager = ConfigManager()
    user_config = cfg_manager.get_user_config()
    base_dir = user_config.get('base_dir')
    assert base_dir is not None and isinstance(base_dir, str) and len(base_dir) > 0

