# UpgrAIder

UpgrAIder is a tool for automatically updating outdated code snippets (specifically those that use deprecated library APIs). The underlying technique relies on the usage of a Large Language Model (hence the "AI" in the name), augmented with information retrieved from release notes. More details about the project can be found in [this presentation](https://github.com/githubnext/Upgraider/blob/main/Show-and-Tell/Nadi_ShowAndTell.pdf).

Note that UpgrAIder represents an early exploration of the above technique, and has been made available in open source as a basis for research and exploration.

## Setup

- `git clone <this repo>`

- Install dependencies:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements
python setup.py develop
```

- Create environment variables
	- You will need an OpenAI key to run this project. 	
	- When running evaluation experiments, we use a separate virtual environment to install the specific version of the library we want to analyze. Create a virtual environment in a separate folder from this project and include its path in the `.env file` (`SCRATCH_VENV`) 
	- Create a `.env` file to hold these environment variables:
	
	```
	cat > .env <<EOL
	OPENAI_API_KEY=...
	OPENAI_ORG=...
	SCRATCH_VENV=<path to a folder that already has a venv we can activate>
	```

## Running

### Populating the DB

To populate the database with the information of the available release notes for each library, run `python src/upgraider/populate_doc_db.py`

Note that this is a one time step (unless you add libraries or release notes). The `libraries` folder contains information for all current target libraries, including the code examples we evaluate on. Each library folder contains a `library.json` file that specifies the base version, which is the library version available around the training date of the model (~ May 2022) and the current version of the library. The base version is useful to know which release notes to consider (those after that date) while the current version is useful since this is the one we want to use for our experiments.

Right now, each library folder already contains the release notes between the base and current library version. These were manually retrieved; in the future, it would be useful to create a script that automatically retrieves release notes for a given library.

The above script looks for sections with certain keywords related to APIs and/or deprecation. It then creates a DB entry which has an embedding for the content of each item in those sections.

### Updating a single code example

`src/upgraider/fix_code_examples.py` is the file responsible for this. Run `python upgraider/fix_lib_examples.py --help` to see the required command lines. To run a single example, make sure to specify `--examplefile`; otherwise, it will run on all the examples available for that library.

### Running a full experiment

Run `python src/upgraider/run_experiment.py`. This will attempt to run upgraider on *all* code examples avaiable for *all* libraries in the `libraries` folder. The output data and reports will be written to the `output` folder.

### Using Actions to run experiments

The `run_experiment` workflow allows you to run a full experiment on the available libraries. It produces a markdown report of the results. Note that you need to set the required environment variables (i.e., API keys etc) as repository secrets.

### Running Tests

`python -m pytest`

## Extra Functionality

Experimental/not current used any more: To find differences between two versions of an API, you can run

`python src/apiexploration/run_api_diff.py`

which will use the library version info in the `libraries` folders.

# License

This project is licenses under the terms of the MIT open source license. Pleare refer to [MIT](https://github.com/githubnext/UpgrAIder/blob/main/LICENSE) for the full terms.

# Maintainers

- Sarah Nadi (@snadi)
- Max Schaefer (@max-schaefer)

# Support

UpgrAIder is a research prototype and is not officially supported. However, if you have questions or feedback, please file an issue and we will do our best to respond.
