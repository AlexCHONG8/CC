# Verify Work Command

Comprehensive code review command that analyzes recent changes for:
- Best coding practices
- Efficiency and performance
- Security vulnerabilities
- Code quality issues

## Usage

```bash
/verify-work
```

## What it checks

### 1. Code Quality
- Code style and formatting consistency
- Proper error handling
- Documentation completeness
- Type safety (where applicable)
- Code duplication

### 2. Security
- SQL injection vulnerabilities
- XSS risks
- Hardcoded secrets/credentials
- Dependency vulnerabilities
- Input validation
- Authentication/authorization issues

### 3. Efficiency
- Performance bottlenecks
- Inefficient algorithms
- Resource leaks
- Unnecessary computations
- Database query optimization
- Caching opportunities

### 4. Best Practices
- SOLID principles
- DRY (Don't Repeat Yourself)
- Separation of concerns
- Proper testing coverage
- Git commit quality
- Documentation clarity

## Output Format

The command provides:
- ✅ **Passed checks**: What looks good
- ⚠️ **Warnings**: Minor issues to consider
- ❌ **Critical issues**: Problems that should be fixed
- 💡 **Recommendations**: Improvement suggestions
- 📊 **Summary**: Overall quality score
