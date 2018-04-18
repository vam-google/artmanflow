# Artmanflow
Workflow wrapper around https://github.com/googleapis/artman

### Prerequisites
- Installed docker, commands `docker run` and `docker pull` work normally (do not require sudo permissions)
- Python 2.7+
- `pip install flask` 
- `pip install ruamel.yaml`
- `pip install github3.py`

### Current state
- The tool can generate java batches PR to staging without need of any manual interruption/hacking (hopefully) with few button clicks.
- The maven publishing steps are not implemented yet.

### Usage

1. To start web-mode (highly recommended option): `FLASK_APP=artmanflow/web/index.py python -m flask run`, then go to `http://127.0.0.1:5000/` in your browser.

2. **(Optional)** To run individual step manually in a docker (using source generation step as example):
    1. Edit (optional) `artmanflow/web/templates/sources_generation.yaml`
    2. Run `python artmanflow/steps/sources_generation_host.py artmanflow/web/templates/sources_generation.yaml`
3. **(Optional)** To run individual step on local machine (not in docker), using source generation step as example:
    1. Edit (note all the paths in the config should be local machine-specific) `artmanflow/web/templates/sources_generation.yaml`
    2. Run 'python artmanflow/steps/sources_generation_guest.py artmanflow/web/templates/sources_generation.yaml

In case of the option (1) the overall usage of the tool should be intuitive, if no, please let me know.

### The overall tool structure
- `artmanflow/steps` contains `*_host.py` and `*_guest.py` scripts for each implemented step. The host script prepares environment and then runs the guest script in docker. The guest script is the script which does the actual work. Both scripts can be run individually in "standalone" mode, for guest scripts linux environment is assumed.
- The `artmanflow/web` directory contains files to support running the stuff from web-ui.
- The web-ui tries to organize the whole process in a form of a workflow.
- Each "step" in the workflow implements some reasonably big self-contained chunk of work. The steps are separated by mandatory (for our process as we have it now) "approval" (i.e. manual) steps (like approve automatically generated PR).
- The wool allows to checkout development versions of artman/toolkit/googleapis during generation and use them (or mount local directory for any of those); this allows to not wait until new artman docker image builds in case if there are some updates/fixes in googleapis or toolkit (which is very often the case).

### Some useful "undocumented" features
- It supports mounting your local directory instead of gitrepo (for googleapis, artman, toolkit). To do so specify the git repo path in a form of: `file:///full/path/on/your/system/to/git/repo`. If this is specified, the branch/commit fields will be ignored and the local directory is assumed to have all in desired state, and will be used by generation script as is.

- In case if the "Debug Mode" is selected on execution, the tool will copy internal docker relevant files (like corresponding cheked out/modified repos) in the `/tmp` directory of the host machine. With this option, one can troubleshoot generation process and/or do manual edits of the generated stuff. For example, on the staging step, to do some modifications in posted PR and push an 'amendment' commit without need to checkout the branch separately: just go to the `/tmp/java-src-stage-<execution_id>/guest_output/guest_root_dir_snapshot`, the checked out repo will be there, available for manual modifications if required. The link to the actual `/tmp/java-src-stage-<execution_id>` is provided at the top of the execution output page for each step.

