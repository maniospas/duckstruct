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

print(x.type() & y.type() & z.type())
