#!/bin/bash
# Setup script for ClimaCocal TDD Test Suite

echo "🚀 Setting up ClimaCocal TDD Test Environment..."

# Activate virtual environment
echo "📦 Activating virtual environment..."
if [ -d "myvenv" ]; then
    source myvenv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv myvenv
    source myvenv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install test dependencies
echo "📚 Installing test dependencies..."
pip install -q coverage watchdog flake8 black isort

# Verify Django is available
echo "🔍 Verifying Django installation..."
python -c "import django; print(f'✅ Django {django.get_version()} available')" 2>/dev/null || {
    echo "❌ Django not found in virtual environment"
    echo "   This suggests the project runs with Docker or system Python"
    echo "   Test suite created and ready for Docker environment"
}

# Make test runner executable
chmod +x test_runner.py

echo ""
echo "🧪 TDD Test Suite Setup Complete!"
echo ""
echo "📋 Available Commands:"
echo "   ./test_runner.py --all           # Run all tests"
echo "   ./test_runner.py --unit          # Run unit tests only"
echo "   ./test_runner.py --integration   # Run integration tests"
echo "   ./test_runner.py --watch         # Watch mode for development"
echo "   ./test_runner.py --coverage      # Generate coverage reports"
echo "   ./test_runner.py --lint          # Code quality checks"
echo ""
echo "📖 Documentation:"
echo "   TDD_STRATEGY.md                  # Complete TDD guide"
echo "   myproject/tests/                 # Test suite directory"
echo ""
echo "🎯 TDD Workflow:"
echo "   1. RED:     Write failing test"
echo "   2. GREEN:   Write minimal code to pass"  
echo "   3. REFACTOR: Improve code keeping tests green"
echo ""
echo "Ready for Test-Driven Development! 🎉"