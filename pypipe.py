import subprocess
import re
import collections
import fcntl
import os
import select
import errno
import signal


def sh(cmd, shell=True):
    return Sh(None, cmd, shell)

class Stream(object):
    _stream_classes = {}
    
    def __init__(self, stream):
        if not self._stream_classes:
            self.__reg_class(Stream)

        if stream is None or isinstance(stream, Stream):
            self._stream = stream
        else:
            # assume it's a filename
            self._stream = open(stream)
        
        self.__is_end = False
        
    def __reg_class(self, cls):
        self._stream_classes[cls.__name__] = cls
        for subclass in cls.__subclasses__():
            self.__reg_class(subclass)
    
    def list(self):
        return list(self)

    def __getattr__(self, name):
        cap_name = name.capitalize()
        if cap_name not in self._stream_classes:
            # try to update the inheritance hierarchy 
            self.__reg_class(Stream)
        
        if cap_name in self._stream_classes:
            cls = self._stream_classes[cap_name]
            return lambda *args, **kwargs: cls(self, *args, **kwargs)
        else:
            return None

    
    def __iter__(self):
        for elem in self._do_iter():
            yield elem
            if self.__is_end:
                break
        
        self._end_iter()
    
    def _do_iter(self):
        raise NotImplemented
    
    def _end_iter(self):
        if not self.__is_end:
            self._do_end_iter()
            if self._stream:
                if isinstance(self._stream, Stream):
                    self._stream._end_iter()
                else:
                    # assume it's a file object
                    self._stream.close()
            self.__is_end = True
    
    def _do_end_iter(self):
        pass

class Sh(Stream):
    ''' Run a shell program
    '''

    def __init__(self, stream, cmd, shell=True):
        Stream.__init__(self, stream)
        if shell:
            if not isinstance(cmd, str):
                cmd = ' '.join(cmd)
        else:
            if isinstance(cmd, str):
                cmd = cmd.split()

        self.__cmd = cmd
        if stream:
            if isinstance(stream, Sh):
                stdin_pipe = stream.get_process().stdout
            else:
                stdin_pipe = subprocess.PIPE
        else:
            stdin_pipe = None
            
        self.__p = subprocess.Popen(cmd, shell=shell, 
                                    stdin=stdin_pipe, stdout=subprocess.PIPE,
                                    preexec_fn=self.__subprocess_setup)
    
    def __subprocess_setup(self):
        # Python installs a SIGPIPE handler by default.
        # This is usually not what non-Python subprocesses expect.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        
    def get_process(self):
        return self.__p
    
    def _do_iter(self):
        if not self._stream or isinstance(self._stream, Sh):
            for line in self.__p.stdout.xreadlines():
                yield line
            return
        
        # if the self._stream is not an instance of Sh
        val = fcntl.fcntl(self.__p.stdin, fcntl.F_GETFL)
        fcntl.fcntl(self.__p.stdin, fcntl.F_SETFL, val | os.O_NONBLOCK)
        
        val = fcntl.fcntl(self.__p.stdout, fcntl.F_GETFL)
        fcntl.fcntl(self.__p.stdout, fcntl.F_SETFL, val | os.O_NONBLOCK)

        out_buf = ''
        in_buf = ''
        stream_it = iter(self._stream)
        is_stream_end = False
        rlist = [self.__p.stdout]
        wlist = [self.__p.stdin]
        while True:
            rfds, wfds, _ = select.select(rlist, wlist, [])
            
            if self.__p.stdout in rfds:
                # read things out
                p_out = self.__p.stdout.read()
                if len(p_out) == 0:
                    i_start = 0
                    while i_start < len(out_buf):
                        i_new_line = out_buf.find('\n', i_start)
                        if i_new_line == -1:
                            yield out_buf[i_start:]
                            break
                        else:
                            yield out_buf[i_start:(i_new_line + 1)]
                            i_start = i_new_line + 1
                    break # process exits, so we break the outer loop to quit
                else:
                    out_buf += p_out
                    i_start = 0
                    while i_start < len(out_buf):
                        i_new_line = out_buf.find('\n', i_start)
                        if i_new_line == -1:
                            break
                        else:
                            yield out_buf[i_start:(i_new_line + 1)]
                            i_start = i_new_line + 1
                    if i_start == len(out_buf):
                        out_buf = ''
                    else:
                        out_buf = out_buf[i_start:]
            
            if self.__p.stdin in wfds and not is_stream_end:
                try:
                    in_buf = stream_it.next()
                except StopIteration:
                    is_stream_end = True
                    self.__p.stdin.close()
                    wlist = []

                while in_buf:
                    # python has ignore SIGPIPE on startup,
                    # so os.write will return EPIPE directly.
                    try:
                        #print 'write in_buf:', in_buf
                        n = os.write(self.__p.stdin.fileno(), in_buf)
                        in_buf = in_buf[n:]
                    except IOError, e:
                        if e.errno == errno.EPIPE:
                            # stdin has been closed, so no need to write to it
                            wlist = []
                            break
        
        # before return, we close the stdin because we don't need it.
        self.__p.stdin.close()
        return 

    def _do_end_iter(self):
        self.__p.stdout.close()
        self.__p.wait()

class Grep(Stream):
    def __init__(self, stream, pattern):
        Stream.__init__(self, stream)
        self.__regex = re.compile(pattern)
    
    def _do_iter(self):
        for elem in self._stream:
            if self.__regex.search(elem):
                yield elem

class Col(Stream):
    def __init__(self, stream, column, sep=None, newline=True):
        Stream.__init__(self, stream)
        self.__column = column
        self.__sep = sep
        self.__line_end = '\n' if newline else ''
    
    def _do_iter(self):
        col = self.__column
        line_end = self.__line_end
        for line in self._stream:
            cols = line.split(self.__sep)
            yield (cols[col] if col < len(cols) else '') + line_end

class Head(Stream):
    def __init__(self, stream, line_num = 10):
        Stream.__init__(self, stream)
        self.__line_num = line_num if line_num > 0 else 10
        
    def _do_iter(self):
        for line_num, line in enumerate(self._stream):
            if line_num < self.__line_num:
                yield line
                if line_num == self.__line_num - 1:
                    return
            
class Tail(Stream):
    def __init__(self, stream, line_num = 10):
        Stream.__init__(self, stream)
        self.__line_num = line_num 
        
    def _do_iter(self):
        last_lines = collections.deque()
        stream_iter = iter(self._stream)
        while len(last_lines) < self.__line_num:
            try:
                last_lines.append(stream_iter.next())
            except StopIteration:
                break
        
        for line in stream_iter:
            last_lines.popleft()
            last_lines.append(line)

        for line in last_lines:
            yield line

class Filter(Stream):
    def __init__(self, stream, func):
        Stream.__init__(self, stream)
        self.__func = func

    def _do_iter(self):
        for elem in self._stream:
            if self.__func(elem):
                yield elem

class Map(Stream):
    def __init__(self, stream, func):
        Stream.__init__(self, stream)
        self.__func = func

    def _do_iter(self):
        for elem in self._stream:
            yield self.__func(elem)
