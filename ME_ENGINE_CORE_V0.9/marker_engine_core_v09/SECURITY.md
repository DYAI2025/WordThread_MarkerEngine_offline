# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it to us as follows:

1. **Do not** create a public GitHub issue
2. Email security concerns to: security@marker-engine.dev
3. Include detailed information about the vulnerability
4. Allow reasonable time for us to respond and fix the issue

## Security Considerations

### API Security
- The API uses environment-based CORS configuration
- Input validation is performed using Pydantic models
- Rate limiting should be implemented at the infrastructure level
- API keys should be used for production deployments

### Data Protection
- No personal data is stored by default
- Conversation analysis is performed in-memory
- Artifacts are stored locally and should be secured
- Database integration should use encrypted connections

### Dependencies
- All dependencies are pinned to specific versions
- Regular security audits of dependencies are recommended
- Use `pip audit` or similar tools to check for vulnerabilities

### Configuration Security
- Sensitive configuration should use environment variables
- Never commit secrets to version control
- Use strong, randomly generated secret keys
- Rotate API keys regularly

### Container Security
- Use non-root user in Docker containers
- Keep base images updated
- Scan containers for vulnerabilities
- Use read-only filesystems where possible

## Security Best Practices

1. **Input Validation**: All inputs are validated using Pydantic
2. **Error Handling**: Sensitive information is not exposed in error messages
3. **Logging**: Avoid logging sensitive data
4. **HTTPS**: Always use HTTPS in production
5. **Updates**: Keep dependencies and base images updated
6. **Access Control**: Implement proper authentication and authorization
7. **Monitoring**: Monitor for suspicious activity
8. **Backup**: Regular backups of critical data

## Responsible Disclosure

We kindly ask security researchers to:

- Give us reasonable time to fix issues before public disclosure
- Avoid accessing or modifying user data
- Avoid denial of service attacks
- Avoid spamming our systems

We will acknowledge receipt of your report within 48 hours and provide regular updates on our progress.
