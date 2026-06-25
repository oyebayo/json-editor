from setuptools import find_packages, setup

setup(
    name="json-editor",
    version="1.1.1",
    description="A JSON editor",
    author="sinistrian",
    author_email="oyebayo@gmail.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "editor": ["ui/styles/*"],
    },
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "json-editor = editor.main:main",
        ],
    },
)
