#!/bin/bash
USER=$(whoami)

if [ -z "$SSH_ORIGINAL_COMMAND" ]; then
    sudo asciinema rec /home/$USER/.$USER_rec.log
    exec ${SSH_ORIGINAL_COMMAND}
fi
