# filepath: /media/sheshank/Work_Code/Work_folders/code/visualstudio/shravs/shravs_utils/setup.py
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="shravs-utils",  # Replace with your package name
    version="0.0.1",  # This should match the current_version in .bumpversion.cfg
    author="Sheshank Joshi",
    author_email="sheshank.joshi@gmail.com",
    description="A concise description of your package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SheshankJoshi/shravs-utils",  # Update with your repo URL
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
