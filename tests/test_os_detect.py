import os
import shutil
from unittest.mock import patch
from tacz.utils.os_detect import get_os_info, get_available_tools

class TestOsDetect:
    def test_get_os_info_linux(self):
        """Test OS detection on Linux."""
        with patch('platform.system', return_value='Linux'), \
             patch.dict(os.environ, {'SHELL': '/bin/bash'}):
            info = get_os_info()
            assert info['os'] == 'Linux'
            assert info['shell'] == 'bash'
            assert info['path_sep'] == os.sep
    
    def test_get_os_info_mac(self):
        """Test OS detection on macOS."""
        with patch('platform.system', return_value='Darwin'), \
             patch.dict(os.environ, {'SHELL': '/bin/zsh'}):
            info = get_os_info()
            assert info['os'] == 'macOS'
            assert info['shell'] == 'zsh'
            assert info['path_sep'] == os.sep
    
    def test_get_os_info_windows(self):
        """Test OS detection on Windows."""
        with patch('platform.system', return_value='Windows'), \
             patch.dict(os.environ, {'PSModulePath': 'C:\\Modules'}):
            info = get_os_info()
            assert info['os'] == 'Windows'
            assert info['shell'] == 'PowerShell'
            assert info['path_sep'] == os.sep
    
    def test_get_os_info_windows_cmd(self):
        """Test OS detection on Windows with CMD."""
        with patch('platform.system', return_value='Windows'), \
             patch.dict(os.environ, {}, clear=True):
            info = get_os_info()
            assert info['os'] == 'Windows'
            assert info['shell'] == 'CMD'
            assert info['path_sep'] == os.sep
    
    def test_get_available_tools(self):
        """Test detection of available tools."""
        def mock_which(command):
            available = {
                'git': '/usr/bin/git',
                'python': '/usr/bin/python',
                'docker': None
            }
            return available.get(command)
        
        with patch('shutil.which', side_effect=mock_which):
            tools = get_available_tools()
            assert tools['git'] is True
            assert tools['python'] is True
            assert tools['docker'] is False
    
    def test_get_available_tools_real(self):
        """Test detection of available tools with real system checks."""
        tools = get_available_tools()
        
        assert tools['python'] is True
        
        if shutil.which('git'):
            assert tools['git'] is True
        else:
            assert tools['git'] is False
        
        if shutil.which('docker'):
            assert tools['docker'] is True
        else:
            assert tools['docker'] is False