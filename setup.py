"""Setup configuration for Identity Correlation Engine"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="identity-correlation-engine",
    version="1.0.0",
    author="Rafi Chowdhury",
    author_email="rafi@example.com",
    description="Enterprise identity deduplication and unification platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/identity-correlation-engine",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration :: Authentication/Logout",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.9",
    install_requires=[
        "phonetics>=1.0.0",
        "pyyaml>=6.0",
        "python-levenshtein>=0.21.0",
        "requests>=2.31.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "identity-engine=identity_engine.cli:main",
        ],
    },
)
