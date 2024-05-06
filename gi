#!/bin/sh
# gi tstatus -> git status
firstarg=${1#t}
shift
if [ $# -gt 0 ]; then
    echo "+ Correcting to 'git $firstarg $*'" 1>&2
    exec git "$firstarg" "$@"
else
    echo "+ Correcting to 'git $firstarg'" 1>&2
    exec git "$firstarg"
fi
