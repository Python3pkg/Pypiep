Pypipe
======

Write shell pipeline in Python with your favorite Python syntax.


For example, you can write a pipeline in Python like the following:

```python
a = pypipe.sh("find . -name *.py").grep('test').head(10).list()
```

And the above code will return a list containing the first 10 python filename including 'test' as its substring.

Intro
======

To use pypipe, just import it, and use its sh as entry point, like the following example:

```python
import pypipe

for line in pypipe.sh("find . -name *.py").grep('test').head(10):
    # do whatever you want for each line
```

After you after call the `sh` function, you can use other useful tool like `grep` or `head` to chain the "pipeline",
separated by `.` instead of `|`.
And you can use it in a for loop so that you can iterate over the result easily.
