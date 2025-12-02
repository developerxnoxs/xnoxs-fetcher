# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 4.x.x   | :white_check_mark: |
| 3.x.x   | :white_check_mark: |
| 2.x.x   | :x:                |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability within XnoxsFetcher, please follow these steps:

### Do NOT

- **Do not** open a public GitHub issue for security vulnerabilities
- **Do not** disclose the vulnerability publicly before it has been addressed
- **Do not** exploit the vulnerability for malicious purposes

### Do

1. **Email us directly** at: **developerxnoxs@gmail.com**
2. **Include** the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact of the vulnerability
   - Any suggested fixes (if available)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Investigation**: We will investigate and validate the reported vulnerability
- **Updates**: We will keep you informed about our progress
- **Resolution**: We will work to release a patch as quickly as possible
- **Credit**: With your permission, we will credit you in the release notes

### Timeline

- **48 hours**: Initial acknowledgment
- **7 days**: Initial assessment and response
- **30 days**: Target resolution time for critical vulnerabilities
- **90 days**: Maximum disclosure timeline

## Security Best Practices

When using XnoxsFetcher, please follow these security best practices:

### Credentials Management

```python
# DO: Use environment variables for credentials
import os
username = os.environ.get("TRADINGVIEW_USERNAME")
password = os.environ.get("TRADINGVIEW_PASSWORD")

# DON'T: Hardcode credentials in your code
# username = "myusername"  # NEVER DO THIS
# password = "mypassword"  # NEVER DO THIS
```

### Session Files

- Keep session files (`*.session`, `session_data.json`) private
- Add them to your `.gitignore`
- Never commit session files to version control

### API Usage

- Respect TradingView's terms of service
- Implement rate limiting in your applications
- Don't share authenticated sessions across different applications

## Known Security Considerations

### Session Storage

XnoxsFetcher stores session data locally for persistence. This includes:
- Authentication tokens
- Session cookies
- User preferences

These are stored in plain text for usability. For sensitive environments:
- Use secure file permissions
- Consider encrypting at rest
- Regularly rotate sessions

### Network Security

- All communication with TradingView uses HTTPS
- WebSocket connections use secure WSS protocol
- No sensitive data is logged by default

## Scope

This security policy covers:
- The XnoxsFetcher Python package
- Official documentation
- Official examples and demos

This policy does NOT cover:
- Third-party integrations
- User applications built with XnoxsFetcher
- TradingView's platform itself

## Contact

For security-related inquiries:
- **Email**: developerxnoxs@gmail.com
- **Subject**: [SECURITY] Brief description

Thank you for helping keep XnoxsFetcher and its users safe!
