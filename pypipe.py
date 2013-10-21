import subprocess
import re
import collections


def sh(cmd, shell=True):
    return Sh(None, cmd, shell)

class Stream(object):
    _stream_classes = {}
    
    def __init__(self, stream):
        if not self._stream_classes:
            self.__reg_class(Stream)

        self._stream = stream
        print stream.__class__.__name__, 'stream'
        
        self.__is_end = False
        
    def __reg_class(self, cls):
        self._stream_classes[cls.__name__] = cls
        for subclass in cls.__subclasses__():
            self.__reg_class(subclass)

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
            print self.__class__.__name__, 'end iter'
            if self._stream:
                print 'call instream _end_iter' 
                self._stream._end_iter()
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
        stdin_pipe = subprocess.PIPE if stream else None
        self.__p = subprocess.Popen(cmd, shell=shell, 
                                    stdin=stdin_pipe, stdout=subprocess.PIPE)
        print 'hello'
        
    def get_process(self):
        return self.__p
    
    def _do_iter(self):
        if self._stream:
            for line in self._stream:
                print 'in sh:', line
                self.__p.stdin.write(line)
            self.__p.stdin.close()
        
        for line in self.__p.stdout.xreadlines():
            yield line
    
    def _do_end_iter(self):
        self.__p.stdout.close()
        self.__p.wait()
        print self.__cmd, 'process done'

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