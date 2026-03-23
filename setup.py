"""Setup script for rustchain Python SDK."""

from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rustchain",
    version="0.1.0",
    description="Python SDK for RustChain blockchain",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="RustChain Bounty Hunter",
    author_email="bounty@rustchain.org",
    url="https://github.com/Scottcjn/rustchain-python-sdk",
    license="MIT",
    packages=find_packages(exclude=["tests", "examples"]),
    python_requires=">=3.7",
    install_requires=[
        "httpx>=0.22.0",
    ],
    extras_require={
        "async": ["httpx[http2]>=0.22.0"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Office/Business :: Financial",
    ],
    keywords="rustchain blockchain cryptocurrency sdk",
    entry_points={
        "console_scripts": [
            "rustchain=rustchain.cli:main",
        ],
    },
)
