#!/bin/bash
# Check out Arcanist locally and run it

if ! [ -x ~/src/arcanist/bin/arc ]; then
    echo "Arcanist not found in ~/src/arcanist, will install it for you" 1>&2
    sudo apt-get install php5-cli php5-curl -y
    mkdir -p ~/src
    cd ~/src
    test -d ~/src/libphutil || git clone https://github.com/phacility/libphutil.git ~/src/
    test -d ~/src/arcanist || git clone https://github.com/phacility/arcanist.git ~/src/
    # maybe ln -s ~/src/arcanist/bin/arc ~/bin/local/ so this script is skipped next time
fi

exec ~/src/arcanist/bin/arc "$@"
