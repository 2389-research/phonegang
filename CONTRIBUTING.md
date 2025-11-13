# Contributing to Phonegang

Thank you for your interest in contributing to Phonegang! We welcome contributions from the community.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Android device with USB debugging enabled
- ADB (Android Debug Bridge)
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup Development Environment

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/phonegang.git
cd phonegang
```

2. Install dependencies:
```bash
uv sync
# or with pip
pip install -e ".[dev]"
```

3. Connect an Android device and verify:
```bash
adb devices
phonegang devices
```

## Development Workflow

### Running Tests

Run the test suite before submitting changes:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=phonegang

# Run specific test file
uv run pytest tests/test_accessibility_tree.py -v
```

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and reasonably sized
- Add type hints where appropriate

### Adding New Features

1. Check existing issues or create a new one to discuss the feature
2. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Write tests for your feature (TDD approach recommended)
4. Implement the feature
5. Ensure all tests pass
6. Update documentation as needed
7. Submit a pull request

### Project Structure

```
phonegang/
├── phonegang/              # Main package
│   ├── __init__.py        # Package exports
│   ├── device_manager.py   # Device discovery
│   ├── adb_wrapper.py      # ADB operations
│   ├── accessibility_tree.py  # UI tree parsing
│   ├── controller.py       # High-level automation
│   ├── cli.py             # Command-line interface
│   ├── mcp_server.py      # MCP server implementation
│   ├── mcp_http.py        # HTTP MCP transport
│   ├── http_api.py        # REST API
│   ├── web_viewer.py      # Web viewer
│   └── scrcpy_wrapper.py  # scrcpy integration
├── tests/                 # Test files
├── docs/                  # Documentation
└── pyproject.toml        # Project configuration
```

### Writing Tests

- Place test files in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test function names
- Mock external dependencies (ADB, devices, etc.)
- Test both success and error cases

Example:
```python
def test_find_element_by_text():
    """Test finding UI element by text content."""
    tree = AccessibilityTree(sample_xml)
    element = tree.find_one(text="Login")
    assert element is not None
    assert element.text == "Login"
```

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the issue
- **Steps to reproduce**: Exact steps to trigger the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**:
  - Python version
  - Operating system
  - Android device model and OS version
  - Phonegang version
- **Logs/Screenshots**: Any relevant error messages or screenshots

### Feature Requests

When suggesting features, please describe:

- **Use case**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches you've considered
- **Additional context**: Examples, mockups, or related projects

## Pull Request Process

1. **Update documentation**: Ensure README and docs are updated
2. **Add tests**: New features must include tests
3. **Pass all tests**: Run `uv run pytest` before submitting
4. **Follow code style**: Maintain consistency with existing code
5. **Write clear commits**: Use descriptive commit messages
6. **Update CHANGELOG**: Add entry for significant changes
7. **Reference issues**: Link related issues in PR description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #(issue number)

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for changes
- [ ] Tested with real Android device

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or clearly documented)
```

## Code Review Process

- Maintainers will review PRs as time permits
- Reviews may request changes or clarifications
- Be responsive to feedback
- Once approved, maintainers will merge the PR

## Community Guidelines

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions
- Help others learn and grow

## Questions?

- Open an issue for questions about contributing
- Check existing issues and documentation first
- Be patient - maintainers are volunteers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
