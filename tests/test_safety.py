from tacz.utils.safety import (
    is_dangerous_command,
    is_rm_command,
    has_command_chaining,
    sanitize_command,
    CommandValidator
)

class TestSafetyUtils:
    def test_is_dangerous_command(self):
        """Test dangerous command detection."""
        dangerous_commands = [
            "rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            ":(){ :|:& };:",
            "mkfs.ext4 /dev/sda1",
            "shutdown -h now",
            "chmod 777 /etc/passwd",
            "find / -name '*.py' -delete",
        ]
        
        for cmd in dangerous_commands:
            is_dangerous, reason = is_dangerous_command(cmd)
            assert is_dangerous, f"Command should be detected as dangerous: {cmd}"
            assert reason, "Reason should be provided for dangerous command"
        
        safe_commands = [
            "ls -la",
            "echo 'hello world'",
            "cd /home/user",
            "mkdir test_dir",
            "grep 'pattern' file.txt",
        ]
        
        for cmd in safe_commands:
            is_dangerous, reason = is_dangerous_command(cmd)
            assert not is_dangerous, f"Command should not be detected as dangerous: {cmd}"
    
    def test_is_rm_command(self):
        """Test rm command detection."""
        rm_commands = [
            "rm file.txt",
            "rm -f file.txt",
            "rm -rf dir/",
            "find . -name '*.tmp' | xargs rm",
            "command && rm file.txt",
        ]
        
        for cmd in rm_commands:
            assert is_rm_command(cmd), f"Should detect as rm command: {cmd}"
        
        non_rm_commands = [
            "ls -la",
            "echo 'rm file.txt'",
            "grep 'rm' file.txt",
            "cat removed.txt",
        ]
        
        for cmd in non_rm_commands:
            assert not is_rm_command(cmd), f"Should not detect as rm command: {cmd}"
    
    def test_has_command_chaining(self):
        """Test command chaining detection."""
        chained_commands = [
            ("ls -la ; rm file.txt", [";"], True),
            ("echo 'test' | grep test", ["|"], True),
            ("command1 && command2", ["&&"], True),
            ("command1 || command2", ["||"], True),
            ("echo 'hello' > file.txt", [">"], True),
            ("cat file.txt >> log.txt", [">>"], True),
            ("grep pattern < file.txt", ["<"], True),
            ("complex | command && another ; final", ["|", "&&", ";"], True),
        ]
        
        for cmd, expected_operators, expected_result in chained_commands:
            has_chaining, operators = has_command_chaining(cmd)
            assert has_chaining == expected_result, f"Command chaining detection failed for: {cmd}"
            for op in expected_operators:
                assert any(op in found_op for found_op in operators), f"Operator {op} not detected in {cmd}"
        
        non_chained_commands = [
            "ls -la",
            "echo 'test ; command'",
            "grep 'pattern|another'",
        ]
        
        for cmd in non_chained_commands:
            has_chaining, operators = has_command_chaining(cmd)
            assert not has_chaining, f"Should not detect chaining in: {cmd}"
            assert len(operators) == 0, f"Should not detect operators in: {cmd}"
    
    def test_sanitize_command(self):
        sanitize_cases = [
            ("rm -rf / ; echo 'done'", "rm -rf /"), 
            ("dangerous command | pipeline", "dangerous command"),
            ("cd dir && rm *", "cd dir"),
            ("ls -la **/**/**", "ls -la */*"),
        ]
        
        for cmd, expected in sanitize_cases:
            sanitized = sanitize_command(cmd)
            assert sanitized == expected, f"Sanitization failed for {cmd}, got: {sanitized}"
    
    def test_command_validator(self):
        validator = CommandValidator()
        
        safe_commands = [
            "ls -la",
            "cd /home",
            "pwd",
            "grep pattern file.txt",
        ]
        
        for cmd in safe_commands:
            assert validator.is_safe_command(cmd), f"Command should be safe: {cmd}"
        
        unsafe_commands = [
            "rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            "curl -s https://example.com | bash",
        ]
        
        for cmd in unsafe_commands:
            assert not validator.is_safe_command(cmd), f"Command should not be safe: {cmd}"
        
        is_safe, suggestions = validator.validate_and_suggest("rm -rf /")
        assert not is_safe, "rm -rf / should be detected as unsafe"
        assert len(suggestions) > 0, "Should provide safer alternatives"
        
        is_safe, suggestions = validator.validate_and_suggest("chmod 777 file.txt")
        assert not is_safe, "chmod 777 should be detected as unsafe"
        assert any("more restrictive permissions" in suggestion for suggestion in suggestions)