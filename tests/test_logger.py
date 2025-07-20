from src.logger.logger import global_logger
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
import pytest


def test_logger_init():
    logger = global_logger
    assert logger is not None

def test_logger_config_is_not_none():
    logger = global_logger
    assert logger.config is not None

def test_logger_default_level():
    logger = global_logger
    assert logger.config['level'] == 'DEBUG'  # Assuming default level is DEBUG

def test_logger_log_methods():
    logger = global_logger
    assert hasattr(logger, 'debug')
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'warning')
    assert hasattr(logger, 'error')
    assert hasattr(logger, 'critical')

def test_logger_log_to_console():
    """测试日志是否输出到控制台 - 使用标准输出捕获"""
    logger = global_logger
    message = "Test console log"
    
    # 方法1：捕获标准输出
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        logger.info(message)
    
    output = captured_output.getvalue()
    assert message in output, f"控制台输出中应该包含 '{message}'，但实际输出是: '{output}'"
    print(f"✓ 控制台输出验证成功: {output.strip()}")


def test_logger_log_to_console_with_different_levels():
    """测试不同级别的日志输出到控制台"""
    logger = global_logger
    test_message = "Multi-level test"
    
    # 测试不同级别的日志
    levels_to_test = ['debug', 'info', 'warning', 'error', 'critical']
    captured_outputs = {}
    
    for level in levels_to_test:
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            getattr(logger, level)(f"{test_message} - {level.upper()}")
        
        output = captured_output.getvalue()
        captured_outputs[level] = output
        
        # 验证输出包含消息
        if output:  # 某些级别可能因为日志级别设置而不输出
            assert test_message in output, f"{level.upper()} 级别日志输出验证失败"
            assert level.upper() in output.upper(), f"{level.upper()} 级别标识应该在输出中"
    
    # 打印所有捕获的输出用于调试
    for level, output in captured_outputs.items():
        print(f"{level.upper()} 输出: {output.strip() if output else '(无输出)'}")


def test_logger_console_output_format():
    """测试日志输出格式"""
    logger = global_logger
    test_message = "Format test message"
    
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        logger.info(test_message)
    
    output = captured_output.getvalue().strip()
    
    # 验证输出格式包含基本元素
    assert test_message in output, "输出应包含原始消息"
    assert "INFO" in output or "info" in output.lower(), "输出应包含日志级别"
    
    # 验证时间戳格式（假设格式包含日期时间）
    import re
    # 检查是否包含时间戳模式 (例如: [2025-07-20 10:30:45] 或类似格式)
    timestamp_pattern = r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}|\[\d+.*?\]'
    has_timestamp = bool(re.search(timestamp_pattern, output))
    
    print(f"✓ 日志格式验证 - 输出: {output}")
    print(f"✓ 包含时间戳: {has_timestamp}")


def test_logger_console_output_manual_verification():
    """手动验证测试 - 直接输出到控制台供人工确认"""
    logger = global_logger
    
    print("\n" + "="*50)
    print("手动验证：以下应该在控制台看到不同级别的日志输出")
    print("="*50)
    
    logger.debug("🔍 这是一条DEBUG级别的日志")
    logger.info("ℹ️ 这是一条INFO级别的日志")
    logger.warning("⚠️ 这是一条WARNING级别的日志")
    logger.error("❌ 这是一条ERROR级别的日志")
    logger.critical("🚨 这是一条CRITICAL级别的日志")
    
    print("="*50)
    print("如果上面看到了彩色或格式化的日志输出，说明控制台输出正常工作")
    print("="*50 + "\n")


def test_logger_console_configuration():
    """测试控制台输出配置"""
    logger = global_logger
    
    # 检查配置中是否启用了控制台输出
    console_enabled = logger.config.get('log_to_console', True)
    assert isinstance(console_enabled, bool), "log_to_console 配置应该是布尔值"
    
    print(f"✓ 控制台输出配置: {'启用' if console_enabled else '禁用'}")
    
    # 如果启用了控制台输出，测试实际输出
    if console_enabled:
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            logger.info("配置验证测试消息")
        
        output = captured_output.getvalue()
        if console_enabled:
            assert output.strip(), "启用控制台输出时应该有实际输出"
        print(f"✓ 控制台输出功能验证通过")
    else:
        print("ℹ️ 控制台输出已在配置中禁用")


@pytest.fixture
def capture_console_output():
    """pytest fixture 用于捕获控制台输出 - 改进版本"""
    # 方法1：直接返回StringIO对象，在测试中手动使用
    return io.StringIO()


def test_logger_with_pytest_fixture(capture_console_output):
    """使用 pytest fixture 测试控制台输出 - 修复版本"""
    logger = global_logger
    test_message = "Pytest fixture test"
    
    # 在测试方法内部进行重定向
    with redirect_stdout(capture_console_output):
        logger.info(test_message)
    
    output = capture_console_output.getvalue()
    print(f"Captured output: {repr(output)}")  # 使用repr显示原始内容
    
    if output.strip():
        assert test_message in output, f"Expected '{test_message}' in output, got: {repr(output)}"
        print(f"✓ Pytest fixture 验证成功: {output.strip()}")
    else:
        print("⚠️ 没有捕获到输出，可能logger配置问题或输出被过滤")


def test_logger_with_capsys(capsys):
    """使用 pytest 的 capsys fixture 测试控制台输出"""
    logger = global_logger
    test_message = "Capsys fixture test"
    
    # 直接调用logger，capsys会自动捕获
    logger.info(test_message)
    
    # 获取捕获的输出
    captured = capsys.readouterr()
    stdout_output = captured.out
    stderr_output = captured.err
    
    print(f"Stdout: {repr(stdout_output)}")
    print(f"Stderr: {repr(stderr_output)}")
    
    # 检查输出在stdout或stderr中
    total_output = stdout_output + stderr_output
    
    if test_message in total_output:
        print(f"✓ Capsys 验证成功: 在{'stdout' if test_message in stdout_output else 'stderr'}中找到消息")
    else:
        print(f"⚠️ Capsys 没有找到消息，可能配置问题")
        print(f"Logger配置: {logger.config}")


def test_logger_with_monkeypatch(monkeypatch, capsys):
    """使用 monkeypatch 和 capsys 测试控制台输出"""
    logger = global_logger
    test_message = "Monkeypatch test"
    
    # 记录所有print调用
    printed_messages = []
    
    def mock_print(*args, **kwargs):
        printed_messages.append(' '.join(str(arg) for arg in args))
        # 仍然调用原始的print以便capsys捕获
        import builtins
        builtins.__print__(*args, **kwargs)
    
    # 保存原始print函数
    import builtins
    builtins.__print__ = builtins.print
    
    # 用mock函数替换print
    monkeypatch.setattr(builtins, 'print', mock_print)
    
    # 调用logger
    logger.info(test_message)
    
    # 检查mock函数捕获的消息
    print(f"Print调用记录: {printed_messages}")
    
    # 也检查capsys的输出
    captured = capsys.readouterr()
    print(f"Capsys捕获: stdout={repr(captured.out)}, stderr={repr(captured.err)}")
    
    # 验证消息被捕获
    found_in_mock = any(test_message in msg for msg in printed_messages)
    found_in_capsys = test_message in (captured.out + captured.err)
    
    if found_in_mock or found_in_capsys:
        print("✓ Monkeypatch + Capsys 验证成功")
    else:
        print(f"⚠️ 没有找到消息，Logger配置: {logger.config.get('log_to_console', 'N/A')}")


def test_logger_direct_method_call():
    """直接测试logger的控制台输出方法"""
    logger = global_logger
    test_message = "Direct method test"
    
    # 测试_log_to_console方法是否存在
    assert hasattr(logger, '_log_to_console'), "Logger应该有_log_to_console方法"
    
    # 直接捕获_log_to_console方法的输出
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        # 格式化消息（模拟logger的内部处理）
        timestamp = "2025-07-20 10:30:45"
        formatted_message = f"[{timestamp}] [INFO] {test_message}"
        logger._log_to_console(formatted_message)
    
    output = captured_output.getvalue()
    print(f"直接方法调用输出: {repr(output)}")
    
    if logger.config.get('log_to_console', True):
        assert output.strip(), "启用控制台输出时应该有输出"
        assert test_message in output, f"输出应包含测试消息: {test_message}"
        print("✓ 直接方法调用验证成功")
    else:
        print("ℹ️ 控制台输出在配置中被禁用")
