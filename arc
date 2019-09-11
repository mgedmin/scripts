#!/bin/bash
# Check out Arcanist locally and run it

##BASE_DIR=~/src
BASE_DIR=~/.mozbuild

if ! [ -x $BASE_DIR/arcanist/bin/arc ]; then
    echo "Arcanist not found in $BASE_DIR/arcanist, will install it for you" 1>&2
    sudo apt install php-cli php-curl -y
    mkdir -p $BASE_DIR
    pushd $BASE_DIR || exit 1
    test -d libphutil || git clone https://github.com/phacility/libphutil.git
    test -d arcanist || git clone https://github.com/phacility/arcanist.git
    # maybe ln -sr $BASE_DIR/arcanist/bin/arc ~/bin/local/ so this script is skipped next time
    popd || exit 1
fi

exec $BASE_DIR/arcanist/bin/arc "$@"
