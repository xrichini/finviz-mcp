"""
setup.py
Defines entry point for 'finviz-mcp' command.
Supports both pip install and uv uvx.
"""

from setuptools import setup, find_packages

setup(
    name="finviz-mcp",
    version="0.1.0",
    py_modules=["server"],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "finviz-mcp=server:main",
        ],
    },
)
