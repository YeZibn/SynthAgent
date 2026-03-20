from setuptools import setup, find_packages

setup(
    name="hello-agents",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests==2.31.0",
        "pytest==7.4.0"
    ],
    entry_points={
        "console_scripts": [
            "hello-agent=hello_agents.main:main"
        ]
    }
)