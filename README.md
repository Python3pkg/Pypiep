Pypipe
======

Write shell pipeline in Python with your favorite Python syntax.


For example, you can write a pipeline in Python like the following:

```python
a = pypipe.sh("find . -name *.py").grep('test').head(10).list()
```

And the above code will return a list containing the first 10 python filename including 'test' as its substring.
