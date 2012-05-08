#!/bin/sh

set -e
cd "$(dirname "$0")"

for file in wo-ist-der-eismann.plasmoid ; do
  if [ "$1" == "-f" ]; then
    rm -f "$file"
  else
    [ -e "$file" ] && rm -i "$file"
  fi
  [ -e "$file" ] && exit 1
done
zip -r wo-ist-der-eismann.plasmoid . -x '*~' '*.zip' '.git*' updatejsfiles.sh packageplasmoid.sh runplasmoidviewer.sh

echo "Did you remember, to:"
echo " * Update the version in the .desktop file"
echo " * Probably other stuff? ;-)"
