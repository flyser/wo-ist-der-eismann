#!/bin/sh

set -e
cd "$(dirname "$0")"

if [ -e wo-ist-der-eismann.zip ] ; then
  rm -i wo-ist-der-eismann.zip
  [ -e wo-ist-der-eismann.zip ] && exit 1
fi
zip -r wo-ist-der-eismann.zip . -x '*~' '*.zip' '.git*' updatejsfiles.sh packageplasmoid.sh runplasmoidviewer.sh

echo "Did you remember, to:"
echo " * Update the version in the .desktop file"
echo " * Probably other stuff? ;-)"
