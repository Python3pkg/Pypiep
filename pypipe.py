import subprocess
import re
import collections


def sh(cmd, shell=True):
    return Process(None, cmd, shell)

class Stream(object):
    _stream_classes = {}
    
    def __init__(self, stream):
        if not self._stream_classes:
            self.__reg_class(Stream)

        cls = self.__class__
        if cls.__name__ not in self._stream_classes:
            self.__reg_class(cls)
        
        self._stream = stream
        print stream.__class__.__name__, 'stream'
        
    def __reg_class(self, cls):
        self._stream_classes[cls.__name__] = cls
        for subclass in cls.__subclasses__():
            self._stream_classes[subclass.__name__] = subclass
            self.__reg_class(subclass)

    def __getattr__(self, name):
        cap_name = name.capitalize()
        if cap_name in self._stream_classes:
            cls = self._stream_classes[cap_name]
            return lambda *args, **kwargs: cls(self, *args, **kwargs)
        else:
            return None
    
    def __iter__(self):
        for elem in self._do_iter():
            yield elem
        
        self._end_iter()
    
    def _do_iter(self):
        raise NotImplemented
    
    def _end_iter(self):
        self._do_end_iter()
        print self.__class__.__name__, 'end iter'
        if self._stream:
            print 'call instream _end_iter' 
            self._stream._end_iter()
    
    def _do_end_iter(self):
        pass

class Process(Stream):
    '''
    classdocs
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
        self.__p = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    
    def _do_iter(self):
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
    def __init__(self, stream, column, sep=' '):
        Stream.__init__(self, stream)
        self.__column = column
        self.__sep = sep
    
    def _do_iter(self):
        col = self.__column
        for line in self._stream:
            cols = line.split(self.__sep)
            yield cols[col] if col < len(cols) else ''

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