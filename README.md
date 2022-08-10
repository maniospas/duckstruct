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
z = np.array([7.8])
x = TypeListener(x)
y = TypeListener(y)
z = TypeListener(z)
print(x)
print(x+1)
print(y)
print(x+1+y.sum()+z.sum())
print(z+y.sum())
print(z.sum())
```

After running code, you can view the structure a new variable 
should have to replace (combinations of) others. For example,
*y* is interoperable to variable with data structure in *yaml* format:

```yaml
object:
  __str__: 
    returns:
      class: str
  sum: 
    returns:
      class: int32
```

To infer a common datatype between *x, y, z* run:

```python
print(x.type() & y.type() & z.type())
```

This finds the minimum necessary data structure to replace
all variables in the code with. The result is provided 
in *yaml* format:

```yaml
object:
  __str__: 
    returns:
      class: str
  __add__: 
    returns:
      -  __add__: 
          returns:
            __add__: 
              returns:
                __str__: 
                  returns:
                    class: str
      -  __str__: 
          returns:
            class: str
  sum: 
    -  returns:
        class: int32
    -  returns:
        class: float64
```

List of subtypes (i.e. competing lines starting with `-`)
indicate many possible types. For example, the top-level
`__add__` method should either return a string-callable or
another data structures with a defined addition to be converted
to a string callable.

Notice that call chains can quickly get rather unwieldy. 
But fear not, because `duckstruct` provides a reduction 
mechanism to automatically infer object references. 
To do this, define a namespace as a 
dictionary between class names and structure types
and call the package's reduction method per:


```python
from duckstruct import reduction

namespace = {"CombinedReduced": x.type() & y.type() & z.type()}
namespace = reduction(namespace)
print(namespace["CombinedReduced"])
```

This creates a nice and clean data structure:

```yaml
object:
  class: CombinedReduced
  __str__: 
    returns:
      class: str
  __add__: 
    returns:
      class: CombinedReduced
  sum: 
    -  returns:
        class: int32
    -  returns:
        class: float64
```



# :fire: Usage
* Find minimum necessary duck typing.
* Data structure maintenance (e.g. remove unused methods).
* Write custom data structures for programs of others.
