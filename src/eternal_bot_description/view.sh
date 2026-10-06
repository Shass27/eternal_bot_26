#!/bin/bash
# usage: ./view.sh  (works from any directory)
P=$(cd "$(dirname "$0")" && pwd)   # package root = script location
S=/tmp/urdf_out
mkdir -p "$S" || exit 1
for f in "$P"/urdf/*; do sed "s#\$(find eternal_bot_description)#$P#g" "$f" > "$S/$(basename "$f")"; done
xacro "$S/eternal_bot.xacro" -o "$S/eternal_bot.urdf" || exit 1
urdf-viz "$S/eternal_bot.urdf"
