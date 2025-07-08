"""Setup configuration for the Kworb Spotify Scraper package."""
from setuptools import find_packages, setup

setup(
    name="kworb-spotify-scraper",
    version="1.0.0",
    description="A modern tool for scraping and analyzing Spotify chart data from KWORB.net",
    author="Ralston Raphael",
    author_email="",  # Add your email if you want
    packages=find_packages(include=["src", "src.*"]),
    package_data={
        "src": ["ui/*", "config/*"],
    },
    install_requires=[
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.1",
        "pandas>=2.1.0",
        "tqdm>=4.66.0",
        "retrying>=1.3.4",
        "streamlit>=1.28.0",
        "Flask>=3.0.0",
        "pydantic>=2.5.0",
        "pytest>=7.4.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0.1",
        "typing-extensions>=4.8.0",
        "black>=23.11.0",
        "isort>=5.12.0",
        "mypy>=1.7.0",
        "openai>=1.3.0"
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "kworb-scraper=src.main:main",
        ],
    },
) 