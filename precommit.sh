#!/bin/sh

git pull
# git submodule update --init --recursive
cd conllueditor
git pull
cd ..

echo "New files"
for file in `git ls-files -o | grep -E ".conllu$"`; do
    echo $file
    python3 tools/validate.py $file --lang de
done
echo "--"

echo "Modified files"
for file in `git ls-files -m | grep -E ".conllu$"`; do
    echo $file
    python3 tools/validate.py $file --lang de
done
echo "--"
