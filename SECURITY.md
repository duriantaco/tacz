# Security Policy

## Reporting a Vulnerability

We take the security of Tacz seriously. If you've discovered a security vulnerability, please report it to us privately.

### How to Report

1. **Email**: Send an email to `aaronoh2015@gmail.com` with:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Any suggested fixes (optional)

2. **GitHub Private Security Advisory**: You can also use GitHub's private vulnerability reporting feature.

### What to Expect

- **Disclosure Timeline**: We aim to resolve critical vulnerabilities within 7 days

## Security Considerations

### Local LLM Usage

Tacz runs entirely locally using models like Ollama or llama.cpp. This means:

- ✅ No data is sent to external servers
- ✅ Commands are generated locally
- ✅ Your queries stay on your machine

### Command Safety Features

1. **Pre-execution Safety Checks**
   - Dangerous pattern detection
   - Interactive confirmation for risky commands
   - Command editing before execution

2. **No Auto-execution**
   - Tacz never runs commands automatically
   - Users must explicitly confirm execution
   - All commands are shown before running

3. **Configurable Safety**
   - Users can enable/disable safety checks via config
   - Customizable danger patterns
   - Whitelist of safe commands

### Security Best Practices

When using Tacz:

1. **Review Before Running**: Always review generated commands before execution
2. **Keep Software Updated**: Regularly update Tacz and your LLM provider
3. **Secure Your Models**: Ensure your local models come from trusted sources
4. **Audit Command History**: Periodically review your command history

Thank you for helping keep Tacz secure!