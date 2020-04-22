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
    --fast-valgrind)
        export PYTHONMALLOC=malloc
        prefix="valgrind --log-file=valgrind.log"
        prefix+=" --suppressions=$HOME/.python.supp"
        shift
        ;;
    --valgrind)
        export PYTHONMALLOC=malloc
        prefix="valgrind --log-file=valgrind.log"
        prefix+=" --suppressions=$HOME/.python.supp"
        prefix+=" --track-origins=yes"  # slow but better info
        prefix+=" --malloc-fill=cc"
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
