git init# duckstruct

**Dependencies:** None<br/>
**Developer:** Emmanouil (Manios) Krasanakis<br/>
**Contant:** maniospas@hotmail.com

# :zap: Quickstart
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
After running the code, you can show the structure a new variable 
should have to replace all others in *yaml* format.

```python
print(x.type() & y.type() & z.type())
```

This yields the minimum necessary structure for the code to run:

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