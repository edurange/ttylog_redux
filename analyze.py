#!/usr/bin/env python3

import csv
import string
import sys
import os.path
import logging
import re
import codecs
import datetime

class DevNull:
    def write(self, msg):
        pass

sys.stderr = DevNull()

def remove_ansi_escape_sequences(input_string):
    """Remove the ansi escape sequences"""
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
    result = ansi_escape.sub('',input_string)
    return result

def decode(stream):
    buf = []
    lines = stream.splitlines()
    i_line = 0
    for line in lines:
        i_stream_line = 0
        i_buf = 0
        buf.append([])
        while i_stream_line < len(line):
            # debug prints
            #print('buf: {}'.format(''.join(buf[i_line])))
            #print('     {}'.format(' ' * (i_buf - 1) + '^'))
            #print('line[i_stream_line:i_stream_line + 5]: {}'.format(repr(line[i_stream_line:i_stream_line + 5])))
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
            else:
                if i_buf < len(buf[i_line]):
                    buf[i_line][i_buf] = line[i_stream_line]
                else:
                    buf[i_line] += line[i_stream_line]
                i_buf += 1
                i_stream_line += 1
        buf[i_line].append('\n')
        buf[i_line] = ''.join(buf[i_line])
        i_line += 1
    return ''.join(buf)


def sort_ttylog_lines(line):
    return line[1]

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("usage:\n$ analyze.py <ttylog log file> <csv file>\nexiting.")
        exit(1)
    ttylog = sys.argv[1]
    csv_output_file = sys.argv[2]
    if not os.path.isfile(ttylog):
        print("there's a problem with ttylog!\naborting.")
        exit(1)
    ttylog_file = open(ttylog,'r')
    ttylog_read_data = remove_ansi_escape_sequences(decode(ttylog_file.read()))
    ttylog_lines = ttylog_read_data.splitlines()
    ttylog_file.close()
    ttylog_sessions = {}
    current_session_id = ''
    output_prevous_command = ''
    first_ttylog_line = 0
    root_home_dir = '/root'

    for line in ttylog_lines:
        #Get the tty_sid from first line of the session
        if r'starting session w tty_sid' in line:
            session_id = line.split()[-1]
            ttylog_sessions[session_id] = {}
            current_session_id = session_id
            continue

        #Get the user prompt from the second line of the session
        #Same line is 'User prompt is test@intro'
        if r'User prompt is' in line:
            user_initial_prompt = line.split()[-1]
            ttylog_sessions[current_session_id]['initial_prompt'] = user_initial_prompt
            node_name = line.split('@')[-1]
            root_prompt = 'root@' + node_name
            continue

        #Get the user home directory from third line of the session
        if r'Home directory is' in line:
            home_directory = line.split()[-1]
            ttylog_sessions[current_session_id]['home_dir'] = home_directory
            first_ttylog_line = 1
            continue

        decoded_line = line
        #Get the first user entered command
        if first_ttylog_line:
            ttylog_sessions[current_session_id]['lines'] = []
            user_prompt = ttylog_sessions[current_session_id]['initial_prompt']
            current_working_directory = ttylog_sessions[current_session_id]['home_dir']
            #Sample first line is 'ls;1553743080'
            line_split = decoded_line.split(';')
            line_timestamp = int(line_split[-1])
            line_command = ';'.join(line_split[:-1] )
            first_ttylog_line = 0
            continue

        #Get the commands from lines
        elif ttylog_sessions[current_session_id]['initial_prompt'] in decoded_line:
            #If line is like 'googletest@intro:~$ ls;1554089474', 'google' is output of previous command
            start_of_prompt = decoded_line.find(user_prompt)
            if start_of_prompt > 0:
                output_till_start_of_prompt = decoded_line[:start_of_prompt]
                output_prevous_command += output_till_start_of_prompt + "\n"
                decoded_line = decoded_line[start_of_prompt:]

            ttylog_sessions[current_session_id]['lines'].append([user_prompt, line_timestamp, current_working_directory, line_command, output_prevous_command, 'CMEND'])
            output_prevous_command = ''

            #Sample line is 'test@intro:~$ done;1553743085'
            left_dollar_part, right_dollar_part = decoded_line.split('$',1)
            current_working_directory = left_dollar_part.split(':',1)[-1]
            current_working_directory = current_working_directory.replace('~', ttylog_sessions[current_session_id]['home_dir'] ,1)
            user_prompt = ttylog_sessions[current_session_id]['initial_prompt']
            right_dollar_part = right_dollar_part[1:]
            line_split = right_dollar_part.split(';')
            #if timestamp is not available use -1
            try:
                line_timestamp = int(line_split[-1])
            except ValueError:
                line_timestamp = "Not found"
            line_command = ';'.join(line_split[:-1] )
            continue

        elif root_prompt in decoded_line:
            #Same line is 'google]0;root@intro: ~root@intro:~# done;1554092159'
            start_of_first_prompt = decoded_line.find(root_prompt)
            if start_of_first_prompt > 0:
                output_till_start_of_prompt = decoded_line[:start_of_first_prompt]
                output_prevous_command += output_till_start_of_prompt + "\n"
                decoded_line = decoded_line[start_of_first_prompt:]

            # start_of_last_prompt = decoded_line.rfind(root_prompt)
            # decoded_line = decoded_line[start_of_last_prompt:]

            ttylog_sessions[current_session_id]['lines'].append([root_prompt, line_timestamp, current_working_directory, line_command, output_prevous_command, 'CMEND'])
            output_prevous_command = ''

            left_hash_part, right_hash_part = decoded_line.split('#',1)
            current_working_directory = left_hash_part.split(':',1)[-1]
            current_working_directory = current_working_directory.replace('~', root_home_dir ,1)
            right_hash_part = right_hash_part[1:]
            line_split = right_hash_part.split(';')
            line_timestamp = int(line_split[-1])
            line_command = ';'.join(line_split[:-1] )
            continue



        #Get the session exit line
        elif r'END tty_sid' in decoded_line:
            ttylog_sessions[current_session_id]['lines'].append([user_prompt, line_timestamp, current_working_directory, line_command, output_prevous_command, 'CMEND'])
            output_prevous_command = ''
            continue

        #Get the Command Output line
        elif ttylog_sessions[current_session_id]['initial_prompt'] not in decoded_line and root_prompt not in decoded_line :
            output_prevous_command += decoded_line + "\n"

    #Combining the ttylogs for all the sessions, and Sorting the ttylog lines by time
    sorted_ttylog_lines = []
    for session in ttylog_sessions.values():
        for line in session['lines']:
            sorted_ttylog_lines.append(line)

    sorted_ttylog_lines.sort(key = sort_ttylog_lines)

    #Writing data to CSV
    csvfile = open(csv_output_file,'w', newline='')
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='%', quoting=csv.QUOTE_MINIMAL)

    for line in sorted_ttylog_lines:
        line = line.rstrip('\n\r')
        csvwriter.writerow(line)

    csvfile.close()

