from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="upgraider",
    version="0.1.0",
    description="LLM-based update of code examples",
    author="GitHub Next",
    author_email="nadi@ualberta.ca",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"upgraider": ["resources/**/*"]},
    python_requires="==3.10.6",
    url="https://github.com/githubnext/upgraider",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "upgraider_brush = upgraider.update_brushes_code:main",
            "explore_api= apiexploration.run_api_diff:main"
        ],
    },
)
