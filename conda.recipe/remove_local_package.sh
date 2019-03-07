#!/bin/bash
# USAGE: ./remove_local_package.sh
# ACTION: (1) uninstalls any installed taxbrain package (conda uninstall)
# NOTE: for those with experience working with compiled languages,
#       removing a local conda package is analogous to a "make clean" operation

# uninstall any existing taxbrain conda package
conda list taxbrain | awk '$1=="taxbrain"{rc=1}END{exit(rc)}'
if [[ $? -eq 1 ]]; then
    conda uninstall taxbrain --yes 2>&1 > /dev/null
fi

exit 0