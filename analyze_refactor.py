#!/usr/bin/python

import csv
import string
import sys
import os.path
import logging
import re
import codecs
import datetime

def decode(lines):

    #ESC] OSC – Operating System Command. In xterm, they may also be terminated by BEL character. In xterm, the window title can be set by OSC 0;this is the window title BEL.
    #The sample line for root prompt is ']0;root@intro: ~root@intro:~# id;1554092145'
    osc_reg_expr = re.compile(r'\x1B]0;.*\x07')
    reg_expr_move_cursor = re.compile('^[0-9]*;?[0-9]*H')

    buf = []
    i_line = 0
    for line in lines:
        i_stream_line = 0
        i_buf = 0
        buf.append([])
        while i_stream_line < len(line):
            
            if line[i_stream_line] == '\x08':
                i_buf -= 0 if i_buf == 0 else 1
                i_stream_line += 1
            elif line[i_stream_line] == '\x1b' and line[i_stream_line + 1] == '[':
                i_stream_line += 2
                if line[i_stream_line] == 'K':
                    """ erase to end of line """
                    buf[i_line] = buf[i_line][:i_buf]
                    i_stream_line += 1
                elif (line[i_stream_line] == '@') or (line[i_stream_line] in string.digits and line[i_stream_line + 1] == '@'):
                    """ make room for n characters at cursor """
                    n = int(line[i_stream_line]) if line[i_stream_line] in string.digits else 1
                    i = 0
                    while i < n:
                        if i_buf < len(buf[i_line]):
                            buf[i_line][i_buf] = ''
                        else:
                            buf[i_line] += ''
                        i_buf += 1
                        i += 1
                    i_stream_line += 2 if line[i_stream_line] in string.digits else 1
                elif (line[i_stream_line] == 'C') or (line[i_stream_line] in string.digits and line[i_stream_line + 1] == 'C'):
                    """ move the cursor forward n columns """
                    n = int(line[i_stream_line]) if line[i_stream_line] in string.digits else 1
                    i_buf += n
                    i_stream_line += 2 if line[i_stream_line] in string.digits else 1
                elif (line[i_stream_line] == 'P') or (line[i_stream_line] in string.digits and line[i_stream_line + 1] == 'P'):
                    """ delete n chars  """
                    n = int(line[i_stream_line]) if line[i_stream_line] in string.digits else 1
                    buf[i_line] = buf[i_line][:i_buf] + buf[i_line][i_buf + n:]
                    i_stream_line += 2 if line[i_stream_line] in string.digits else 1
                #If sequence is <0x1b>[2J or <0x1b>[3;J, erase in display. Erasing from the start of the line, to the current cursor position
                elif (line[i_stream_line] in string.digits and ((line[i_stream_line + 1] == ';' and line[i_stream_line + 2] == 'J') or (line[i_stream_line + 1] == 'J'))):
                    i_buf = 0
                    buf[i_line].clear()
                    i_stream_line += 3 if line[i_stream_line + 1] == ';' else 2
                #If sequence is <ox1b>[n;mH, escape it. This is for moving the cursor. <0x1b>[H movies the cursor to first row and column
                elif reg_expr_move_cursor.findall(line[i_stream_line:]):
                    move_cursor_control_characters = reg_expr_move_cursor.findall(line[i_stream_line:])[0]
                    number_of_characters_to_skip = len(move_cursor_control_characters)
                    i_stream_line += number_of_characters_to_skip

            #Eliminiating OSC for root prompt
            elif osc_reg_expr.findall(line):
                line = osc_reg_expr.sub('',line)

            else:
                if i_buf < len(buf[i_line]):
                    #import pdb; pdb.set_trace()
                    buf[i_line][i_buf] = line[i_stream_line]
                else:
                    buf[i_line] += line[i_stream_line]
                i_buf += 1
                i_stream_line += 1
        buf[i_line] = ''.join(buf[i_line])
        i_line += 1
    return buf


def sort_ttylog_lines(line):
    return line[1]

if __name__ == "__main__":

    ttylog = sys.argv[1]
    csv_output_file = sys.argv[2]
        # if not os.path.isfile(ttylog):
        #     logging.critical("there's a problem with ttylog! aborting.")
        #     exit(1)

    ttylog_file = open(ttylog,'r')
    ttylog_read_data = ttylog_file.read()
    ttylog_lines = ttylog_read_data.splitlines()
    ttylog_file.close()
    ttylog_lines = decode(ttylog_lines)
    ttylog_sessions = {}
    current_session_id = ''
    output_prevous_command = ''
    first_ttylog_line = 0
    root_home_dir = '/root'
    node_name = ''
    csvfile = open(csv_output_file,'w', newline='')
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='%', quoting=csv.QUOTE_MINIMAL)
    for line in ttylog_lines:
        csvwriter.writerow(line)
    csvfile.close()
