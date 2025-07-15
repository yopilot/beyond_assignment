from setuptools import setup, find_packages

setup(
    name="reddit-persona-generator",
    version="2.0.0",
    description="Generate detailed user personas from Reddit activity",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "praw>=7.6.0",
        "flask>=2.0.0",
        "tqdm>=4.64.0",
        "numpy>=1.21.0",
        "requests>=2.28.0",
        "accelerate>=0.20.0",
        "safetensors>=0.4.0",
        "tokenizers>=0.14.0",
        "huggingface-hub>=0.15.0",
        "psutil>=5.8.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)