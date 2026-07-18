#!/bin/sh
if [ -x ~/.cargo/bin/bat ]; then
    exec ~/.cargo/bin/bat "$@"
elif [ -x /usr/bin/batcat ]; then
    exec /usr/bin/batcat "$@"
else
    echo "bat is not installed, sudo apt install bat" 1>&2
    echo "or cargo install bat" 1>&2
    exit 1
fi
