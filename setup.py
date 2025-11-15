from setuptools import setup, find_packages
from pathlib import Path


def read_requirements():
    """Read requirements from requirements.txt file."""
    requirements_file = Path(__file__).parent / 'requirements.txt'
    with open(requirements_file, 'r', encoding='utf-8') as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]


setup(
    name="pr-agent-system",
    version="1.0.0",
    packages=find_packages(),
    install_requires=read_requirements(),
    python_requires='>=3.8',
    author="PR Agent Team",
    description="AI-powered comment generation system for branding agency executives",
    long_description=(Path(__file__).parent / "README.md").read_text(encoding='utf-8'),
    long_description_content_type="text/markdown",
)
