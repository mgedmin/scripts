#!/bin/sh
if [ -n "$1" ] && [ -f "$1" ] && ! [ -w "$1" ]; then
    echo "$1 is not writable by you, perhaps you want to"
    echo
    echo "   sudo $0 $@"
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
vimhome=$HOME/src/vim
# the /lib/x86_64-linux-gnu/libtinfo.so.5 check needs explanation:
# shared NFS home between to x86_64 machines, one running ubuntu 12.04, one running ubuntu 10.04
# vim built on 12.04 and links to libtinfo.so.5, which doesn't exist on ubuntu 10.04
if test -x $vimhome/src/vim && test "`uname -m`" = "`cat $vimhome/.arch`" && test -f /lib/x86_64-linux-gnu/libtinfo.so.5; then
    VIMRUNTIME=$vimhome/runtime $vimhome/src/vim "$@"
else
    /usr/bin/vim "$@"
fi
