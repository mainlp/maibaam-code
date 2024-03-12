#!/bin/sh

if [ "$#" -ne 1 ]; then
    echo "Usage: ./launch.sh PATH_TO_CONLLU_FILE"
    exit 2
fi

conllueditor/bin/conlluedit.sh -r $1 --deprels tools/data/deprels.json --language de --validator validate.cfg --shortcuts shortcuts.json 8888
