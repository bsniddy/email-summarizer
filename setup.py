from setuptools import setup, find_packages

setup(
    name="email-summarizer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.1.7",
        "requests>=2.32.3",
        "beautifulsoup4>=4.12.3",
        "chardet>=5.2.0",
        "pypdf>=5.0.1",
        "docx2txt>=0.8",
        "python-dateutil>=2.9.0",
        "pytz>=2024.1",
        "IMAPClient>=3.0.1",
    ],
    entry_points={
        "console_scripts": [
            "email-summarizer=email_summarizer.cli:main",
        ],
    },
    python_requires=">=3.8",
)
