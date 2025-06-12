from setuptools import setup, find_packages

setup(
    name="umaxbot",
    version="0.1.1",
    description="Async framework for building bots for MAX messenger (aiogram-style)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="werdset",
    author_email="vladimirwerdset@gmail.com",
    url="https://github.com/werdset/maxbot",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=1.10.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: AsyncIO",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

