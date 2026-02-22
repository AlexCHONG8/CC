# Verify Work Skill

A comprehensive code verification command that reviews your recent work for best practices, efficiency, and security.

## Installation

The skill is already installed in your project at `.skills/verify-work/`

## Usage

Simply invoke the skill by name:

```bash
/verify-work
```

## What It Does

1. **Analyzes recent changes** - Checks git status and modified files
2. **Security review** - Scans for vulnerabilities, secrets, and unsafe practices
3. **Code quality check** - Reviews style, documentation, and maintainability
4. **Efficiency audit** - Identifies performance bottlenecks and optimization opportunities
5. **Best practices verification** - Ensures SOLID principles and clean code

## Example Output

```
🔍 Code Verification Report

📊 Summary
- Files Changed: 3
- Critical Issues: 1
- Warnings: 2
- Overall Score: 7/10

🚨 Critical Issues
- Hardcoded API key in src/config.py:45
- Missing input validation on user_input

⚠️ Warnings
- Inconsistent naming in utils.py
- Missing docstrings in 2 functions

✅ What Looks Good
- Proper error handling in main.py
- Clean separation of concerns
- Good use of type hints

💡 Recommendations
- Add environment variable for API key
- Consider using pydantic for input validation
- Add pytest tests for critical paths
```

## When to Use

- Before committing code
- After completing a feature
- Before creating a pull request
- During code review
- When learning best practices

## Customization

You can customize the verification criteria by editing:
- `.skills/verify-work/skill.md` - Main verification logic
- `.skills/verify-work/CLAUDE.md` - Usage documentation

## License

MIT License - Feel free to modify and distribute
