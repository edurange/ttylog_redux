#!/bin/bash

if [ -z "$SSH_ORIGINAL_COMMAND" ]; then
    sudo asciinema rec ".$(whoami)_rec.log"
    exec ${SSH_ORIGINAL_COMMAND}
fi
