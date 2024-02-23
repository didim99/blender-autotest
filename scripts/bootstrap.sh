#! /bin/bash

PYTHONS=$(find /usr/bin -regextype egrep -regex ".*/python3.[0-9]+" | sort)

PS3="Select a version to use: "
echo "Available Python versions is:"
select PYTHONVER in $PYTHONS; do
  break
done

echo "Using: ${PYTHONVER}"

$PYTHONVER -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
