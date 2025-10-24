#!/bin/bash
# Development quick-start script
# Runs a complete development cycle: setup -> test -> run CLI -> visualize

set -e  # Exit on error

echo "🚀 Weather-Aware Scheduler - Development Quick Run"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate  # Windows Git Bash
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate  # Linux/Mac
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "🔐 Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install -e ".[dev]" --quiet

# Run tests
echo ""
echo "🧪 Running tests..."
python -m pytest tests/ -v --tb=short || echo "⚠️  Some tests failed"

# Run example scheduling request
echo ""
echo "📅 Testing CLI - Scheduling Example"
echo "-----------------------------------"
python -m src.cli.main schedule "Friday 2pm Taipei meet Alice 60min"

# Generate visualization
echo ""
echo "🎨 Generating workflow visualization..."
python -m src.cli.main visualize

# Check if visualization was created
if [ -f "graph/flow.mermaid" ]; then
    echo "✅ Visualization created: graph/flow.mermaid"
    echo "✅ DOT file created: graph/flow.dot"
    echo ""
    echo "💡 To render as SVG: dot -Tsvg graph/flow.dot -o graph/flow.svg"
else
    echo "⚠️  Visualization not created"
fi

# Run dataset replay
echo ""
echo "📊 Running dataset evaluation..."
python scripts/replay_eval.py --dataset datasets/eval_min5.jsonl

echo ""
echo "✅ Development run complete!"
echo ""
echo "Next steps:"
echo "  - View test results above"
echo "  - Check graph/flow.mermaid for workflow diagram"
echo "  - Run 'python -m pytest tests/ -v' for detailed test output"
echo "  - Run 'python -m src.cli.main schedule \"your request\"' to test scheduling"
