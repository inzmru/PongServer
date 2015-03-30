#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
PongServer

A simple HTTP server for single-user webapps.

"""

import socket
import threading
import time

class Socket_Thread(threading.Thread):
    """
    Thread class dealing with client-server peer sockets
    """

    CONTENT_LENGTH = 'content-length'
#------------------------------------------------------------------------------
    def __init__(self, peer_socket, server):
        threading.Thread.__init__(self)
        self.s = peer_socket
        self.server = server
#------------------------------------------------------------------------------
    def parse_headers(self, headers):
        start_line = headers[0].split()  # TODO: strictier parsing
        mode = start_line[0]
        uri = start_line[1]
        fields = {}
        for N in xrange(len(headers)-1):
            header = headers[N+1].split(':')
            name = header[0].lower()
            value = header[1].strip()
            if name == self.CONTENT_LENGTH:
                value = int(value)  # TODO: exception possible -> BAD REQUEST
            fields[name] = value
        return mode, uri, fields
#------------------------------------------------------------------------------
    def read_socket(self):

        buff = ''
        pos = 0
        headers = []
        got_headers = False
        there_is_content = False
        fields = None

        while (
                not got_headers or
                (
                    there_is_content and
                    len(buff)-pos < fields[self.CONTENT_LENGTH]
                )
            ):
            chunk = self.s.recv(1024)

            if len(chunk) == 0:
                raise IOError('Broken socket')

            # Makes a buffer from a leftover form previous parsing
            # from previous loop, and from data just read. it could be
            # an end of a header line that was left last time and now
            # it is sticked to the new data, what hopefully will bring
            # next header line. (If not - no worries, the loop will go
            # to self.s.recv once more and more, as long as needed)

            buff = buffer(buff[pos:]+chunk)
            pos = 0
            if not got_headers:
                # sparsuj tyle linijek nagłówka ile się da, a resztkę doklei
                # się do bufora (komentarz powyżej)
                while True:
                    # TODO: this is probably suboptimal usage of buffer
                    cflf_pos = buff[pos:].find('\r\n')
                    if cflf_pos == -1:
                        break

                    header = buff[pos:cflf_pos+pos]
                    if len(header) == 0:
                        # Empty header line - the end of header
                        got_headers = True
                    else:
                        headers.append(header)

                    # The position in the buffer is moved by a line plus 2
                    # (this two is a '\r\n' oviously)
                    pos += cflf_pos+2

                    if got_headers:
                        mode, uri, fields = self.parse_headers(headers)
                        there_is_content = (self.CONTENT_LENGTH in fields)
                        break

        return mode, uri, fields, buff[pos:]
#------------------------------------------------------------------------------
    def write_socket(self, code, content, alive):
        data = "HTTP/1.1 {code}\r\n".format(code=code)
        content_len = 0
        if content:
            data += "Content-Type: {content_type}\r\n".format(
                        content_type = content['type'],
                     )
            content_len = len(content['data'])

        data += "Content-Length: {content_len}\r\n"\
                "Connection: {keep}\r\n"\
                "\r\n".format(
                     content_len = content_len,
                     keep = 'keep-alive' if alive else 'close',
                 )
        if content:
            data += content['data']

        went = 0
        while went < len(data):
            sent = self.s.send(data[went:])
            if sent == 0:
                raise IOError('Broken socket')
            went += sent
#------------------------------------------------------------------------------
    def file_serv(self, uri, etag):
        """
        Serve a file

        File to serve are listed in ``self.server.files`` dict

        TODO: Cacheing

        """
        try:
            desc = self.server.files[uri]
        except KeyError:
            return '404 Not Found', {}

        f = open(desc[0], 'rb')
        data = f.read()
        f.close()

        return '200 OK', {
            'type': desc[1],
            'data': data,
        }
#------------------------------------------------------------------------------
    def run(self):

        print "{: <20}".format(time.time() % 86400),
        print '--> {}'.format(self.name)

        alive = True
        while alive:

            # ------ read from ---------------

            try:
                mode, uri, fields, content = self.read_socket()
            except IOError:
                break
            try:
                alive = (fields['connection'].lower() == 'keep-alive')
            except KeyError:
                alive = False

            print "{: <20}".format(time.time() % 86400),
            print self.name, self.s.getpeername()[0], mode, uri,
            print "keep-alive" if alive else "close"

            # ------ build a response --------

            # TODO: this is a stub code
            code, content = self.file_serv(uri, None)

            # ------ write to ----------------

            try:
                self.write_socket(code, content, alive)
            except IOError:
                break

        # ------- close ------------------

        exc = False
        try:
            self.s.shutdown(0)
        except socket.error:
            exc = True
        self.s.close()

        print "{: <20}".format(time.time() % 86400),
        print '<-- {}: {} {}'.format(
                self.name,
                'broken' if alive else 'clean',
                'exception' if exc else 'shutdown',
            )
#------------------------------------------------------------------------------
class App_Server(object):
    def __init__(self, host, port, maxsrvsocks=5):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(maxsrvsocks)

        # TODO: a stub code - this MUST be read from a file
        self.files = {
            '/':            ['./main.html', 'text/html', None, None],
            '/favicon.ico': ['./fav.png', 'image/png', None, None],
            '/kotek':       ['./kotek.png', 'inage/png', None, None],
        }

    def mainloop(self):
        while True:
            (peer_socket, adr) = self.server_socket.accept()
            thread = Socket_Thread(peer_socket, self)
            thread.start()
#------------------------------------------------------------------------------
if __name__ == '__main__':
    App_Server('', 7007).mainloop()

