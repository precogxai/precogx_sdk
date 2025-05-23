from setuptools import setup, find_packages

setup(
    name="precogx-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.20.0",
        "pydantic>=2.0.0",
        "langchain-core>=0.1.0",
    ],
    author="PrecogX",
    author_email="info@precogx.ai",
    description="PrecogX SDK for integrating AI agent telemetry.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/precogx/precogx-sdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 