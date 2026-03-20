# Hello Agents Python

A basic Python project structure for agent-based applications.

## Project Structure

```
Hello-Agents-Python/
├── hello_agents/          # Main package
│   ├── __init__.py        # Package initialization
│   ├── main.py            # Main entry point
│   └── utils/             # Utility functions
│       ├── __init__.py
│       └── helpers.py     # Helper functions
├── tests/                 # Test directory
│   ├── __init__.py
│   └── test_main.py       # Test main module
├── requirements.txt       # Dependencies
├── setup.py               # Package setup
└── README.md              # Project documentation
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Hello-Agents-Python
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Usage

Run the main script:
```bash
python hello_agents/main.py
```

Or use the console script:
```bash
hello-agent
```

## Testing

Run the tests:
```bash
pytest
```
