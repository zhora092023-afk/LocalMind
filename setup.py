from setuptools import setup, find_packages

setup(
    name="localmind",
    version="0.1.0",
    description="AI-агент для анализа кода и генерации интерактивных mindmap",
    author="Твой Telegram",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "aiofiles>=23.0.0",
        "httpx>=0.25.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "localmind=app.cli:main",
        ],
    },
    python_requires=">=3.10",
)