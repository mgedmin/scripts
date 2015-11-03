#!/bin/bash
if [ -n "$1" ] && [ -f "$1" ] && ! [ -w "$1" ]; then
    echo "$1 is not writable by you, perhaps you want to"
    echo
    echo "   sudo $0 $*"
    echo
    read -p "run under sudo? [Y/n/q] " answer
    case "$answer" in
        y|Y|"")
            exec sudo "$0" "$@"
            ;;
        q|Q)
            exit
            ;;
    esac
fi

case "$1" in
    --valgrind)
        prefix="valgrind --log-file=valgrind.log"
        # doesn't suppress anything,
        # https://github.com/python/cpython/blob/master/Misc/README.valgrind
        # explains why
        prefix+=" --suppressions=$HOME/.python.supp"
        shift
        ;;
    --gdb)
        prefix=gdb
        shift
        ;;
    *)
        prefix=
        ;;
esac

vimhome=$HOME/src/vim
if test -x "$vimhome/src/vim"; then
    VIMRUNTIME=$vimhome/runtime $prefix "$vimhome/src/vim" "$@"
else
    /usr/bin/vim "$@"
fi
