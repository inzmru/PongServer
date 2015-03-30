#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Update Dir

Updates directory file with hashes for cacheing
"""

import os
import md5
import re

def update(root, directory_file):
    with open(directory_file, 'rb') as df:
        lines = df.readlines()
        os.chdir(root)
        out = u''

        for line in lines:
            if line[0] != '/':
                out += line
            else:
                ma = re.match(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
                etag_type = ma.group(4)
                file_ = ma.group(2)
                etag = ''
                if etag_type == 'md5':
                    with open(file_, 'rb') as f:
                        m = md5.new()
                        m.update(f.read())
                        etag = m.hexdigest()
                elif etag_type == '---':
                    etag = ''

                out += ma.group(0) + ' ' + etag + '\n'

    f = open(directory_file, 'wb')
    f.write(out)
    f.close()

if __name__ == '__main__':
    update('.', 'directory')






