import subprocess
import re

def sh(cmd, shell=True):
    return Process(cmd, shell)

class Stream(object):
    _stream_classes = {}
    
    def __init__(self):
        if not self._stream_classes:
            self.__get_subclasses(Stream)
        
    def __get_subclasses(self, c):
        for subclass in c.__subclasses__():
            self._stream_classes[subclass.__name__] = subclass
            self.__get_subclasses(subclass)
    
    def __getattr__(self, name):
        cap_name = name.capitalize()
        if cap_name in self._stream_classes:
            cls = self._stream_classes[cap_name]
            return lambda *args, **kwargs: cls(self, *args, **kwargs)
        else:
            return None

class Process(Stream):
    '''
    classdocs
    '''

    def __init__(self, cmd, shell=True):
        Stream.__init__(self)
        if isinstance(cmd, str):
            cmd = cmd.split()
        self.__cmd = cmd
        self.__p = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    
    def __iter__(self):
        for line in self.__p.stdout.xreadlines():
            yield line
        
        self.__p.wait()
    
        
class Grep(Stream):
    def __init__(self, stream, pattern):
        Stream.__init__(self)
        self.__stream = stream
        self.__regex = re.compile(pattern)
    
    def __iter__(self):
        for elem in self.__stream:
            if self.__regex.search(elem):
                yield elem

class Col(Stream):
    def __init__(self, stream, column, sep=' '):
        Stream.__init__(self)
        self.__stream = stream
        self.__column = column
        self.__sep = sep
    
    def __iter__(self):
        col = self.__column
        for line in self.__stream:
            cols = line.split(self.__sep)
            yield cols[col] if col < len(cols) else ''