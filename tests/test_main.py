import pytest
from hello_agents.HelloAgentsLLM import main

def test_main():
    assert main() == 0