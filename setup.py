"""
Setup configuration for Shopify SDK
"""

from setuptools import setup, find_packages

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Shopify",
    version="1.0.2",
    author="PKwhiting",
    author_email="",
    description="A Python SDK for interacting with Shopify's GraphQL API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PKwhiting/Shopify",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            # Add console scripts if needed
        ],
    },
    keywords="shopify graphql api sdk ecommerce",
    project_urls={
        "Bug Reports": "https://github.com/PKwhiting/Shopify/issues",
        "Source": "https://github.com/PKwhiting/Shopify",
    },
)