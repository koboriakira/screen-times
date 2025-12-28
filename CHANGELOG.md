# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-28

### Added
- Initial release of screen-times package
- `screenocr` CLI command with subcommands: start, stop, status, split
- macOS screen activity logging with OCR using Vision Framework
- Automatic screenshot capture every 30 seconds
- JSONL-based log storage with date-based organization
- Task-based log splitting functionality
- launchd agent for automatic background execution
- Python 3.9-3.12 support
- Comprehensive test suite with pytest
- CI/CD with GitHub Actions (Ubuntu CI + macOS Build)
- Code quality checks (black, flake8, mypy)
- Pre-commit hooks for automatic code formatting
- Package metadata and documentation for PyPI distribution

### Technical Details
- Package structure reorganized to src layout
- Entry point configuration for pip installation
- PyObjC integration for macOS frameworks (Cocoa, Vision, Quartz)
- Automated testing with platform-specific skipif markers
- Build verification on both Ubuntu and macOS runners
- TestPyPI and PyPI publishing workflows

[Unreleased]: https://github.com/koboriakira/screen-times/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/koboriakira/screen-times/releases/tag/v0.1.0
