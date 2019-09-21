 #!/bin/bash

 if [ -z "$SSH_ORIGINAL_COMMAND" ]; then

     TTY_CMD=$(tty)
     TTY=${TTY_CMD:5}
     #HN=$(hostname)
     HOST=$(hostname)
     #EXP=$(echo $HN | awk -F. '{print $(NF - 1)}')
     #PROJ=$(echo $HN | awk -F. '{print $(NF)}')
     USER=$(whoami)

     sudo mkdir -p /usr/local/src/logs/

     if [ -e "/var/log/ttylog/count.$(hostname)" ]; then
         CNT=$(cat /usr/local/src/logs/count.$(hostname).$(whoami))
         let CNT++
         echo $CNT > /usr/local/src/logs/count.$(hostname).$(whoami)
     else
         sudo touch /usr/local/src/logs/count.$(hostname).$(whoami)
         sudo chmod ugo+rw /usr/local/src/logs/count.$(hostname).$(whoami)
         echo "0" > /usr/local/src/logs/count.$(hostname).$(whoami)
         CNT=$(cat /usr/local/src/logs/count.$(hostname).$(whoami))
     fi

     export TTY_SID=$CNT
     LOGPATH=/usr/local/src/logs/ttylog.$(hostname).$(whoami).$CNT

     sudo touch $LOGPATH
     sudo chmod ugo+rw $LOGPATH

     echo "starting session w tty_sid:$CNT" >> $LOGPATH
     echo "User prompt is ${USER}@${HOST}" >> $LOGPATH
     echo "Home directory is ${HOST}" >> $LOGPATH

     sudo /usr/local/src/ttylog $TTY >> $LOGPATH 2>/dev/null &

     bash
     echo "END tty_sid:$CNT" >> $LOGPATH

 elif [ "$(echo ${SSH_ORIGINAL_COMMAND} | grep '^sftp' )" ]; then

     #sudo touch /var/log/tty.log
     #sudo chmod ugo+rw /var/log/tty.log
     #echo "$SSH_ORIGINAL_COMMAND" >> /var/log/tty.log
     /usr/lib/openssh/sftp-server
     #exec ${SSH_ORIGINAL_COMMAND}

 elif [ "$(echo ${SSH_ORIGINAL_COMMAND} | grep '^scp' )" ]; then

     #HN=$(cat /var/emulab/boot/nickname)
     #HOST=$(echo $HN | awk -F. '{print $(NF - 2)}')
     #EXP=$(echo $HN | awk -F. '{print $(NF - 1)}')
     #PROJ=$(echo $HN | awk -F. '{print $(NF)}')

     #LOGPATH=/var/log/ttylog/ttylog.null.$HOST
     #touch $LOGPATH
     #echo "$SSH_ORIGINAL_COMMAND" >> $LOGPATH
     exec ${SSH_ORIGINAL_COMMAND}

 elif [ "$(echo ${SSH_ORIGINAL_COMMAND})" ]; then

     #HN=$(cat /var/emulab/boot/nickname)
     #HOST=$(echo $HN | awk -F. '{print $(NF - 2)}')
     #EXP=$(echo $HN | awk -F. '{print $(NF - 1)}')
     #PROJ=$(echo $HN | awk -F. '{print $(NF)}')

     #LOGPATH=/var/log/ttylog/ttylog.null.$HOST
     #echo "$SSH_ORIGINAL_COMMAND" >> $LOGPATH
     exec ${SSH_ORIGINAL_COMMAND}

 fi

