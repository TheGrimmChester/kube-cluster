#!/bin/sh
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

if [ "$1" != "--config" ] || [ "$2" != "/path/to/asdf" ] || [ "$3" != "--input-type" ] || [ "$4" != "yaml" ] || [ "$5" != "--output-type" ] || [ "$6" != "yaml" ] || [ "$7" != "--decrypt" ] || [ "$8" != "/dev/stdin" ] || [ "$9" != "" ]; then
    echo "Command (fake-sops-val): $*" > /dev/stderr
    exit 1
fi
if [ "${AWS_SECRET_ACCESS_KEY}" != "yyy" ]; then
    echo "AWS_SECRET_ACCESS_KEY is '${AWS_SECRET_ACCESS_KEY}'" > /dev/stderr
    exit 1
fi
echo 'fake sops output 2'
