#!/bin/bash

export TARGETDIR=~friso/Unsafed/EMS-Data/FileDB/2020

# copy buscounter, calculationcounter, ... from Linear/
scp -r 10.0.0.4:/Smart1/FileDB/2020/Linear/*global*.txt $TARGETDIR/Linear/

# copy raw bus counter data
scp -r 10.0.0.4:/Smart1/FileDB/2020/B* $TARGETDIR/
