# duckstruct

**Dependencies:** None<br/>
**Developer:** Emmanouil (Manios) Krasanakis<br/>
**Contant:** maniospas@hotmail.com

# :zap: Quickstart
Install the package with the command line instruction 
*pip install duckstruct*. Then, use its `TypeListener`
lass to wrap objects.


```python
from duckstruct import TypeListener
import numpy as np

x = np.array([1, 2, 3])
y = np.array([5, 6])
z = np.array([7.])
x = TypeListener(x)
y = TypeListener(y)
z = TypeListener(z)
print(x)
print(x+1+y.sum()+z.sum())
```

After running code, you can view the structure a new variable 
should have to replace (combinations of) others as code inputs.

```python
print(x.type() & y.type() & z.type())
```

This finds the minimum necessary data structure to replace
for the code to run when replacing all variables with it. 
The result is provided in *yaml* format:

```
object:
  __str__: 
    returns:
      class: str
  __add__: 
    returns:
      class: ndarray
  sum: 
    returns:
      -  class: int32
      -  class: float64
```


# :fire: Usage
* Find minimum necessary duck typing
* Maintain data structures (e.g. remove unused methods)
* Write custom data structures for programs
