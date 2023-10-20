#!/bin/bash

module_name=$1
module_version=$2

MAIN_VENV=`pwd`

cd $SCRATCH_VENV

source .venv/bin/activate

pip install jsonpickle

pip uninstall -y $module_name

pip install -q -v "$module_name==$module_version" > /dev/null

pip show $module_name | grep Version

python $MAIN_VENV/src/apiexploration/explore_api.py --module_name=$module_name --module_version=$module_version --main_venv=$MAIN_VENV

deactivate
