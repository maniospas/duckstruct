from duckstruct import TypeListener, reduction
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

print(y.type())

print("======= pre-reduction =======")
print(x.type() & y.type() & z.type())

print("======= reduction =======")
#namespace = reduction({"new_class": x.type() & y.type() & z.type(), "x": x.type()})
namespace = {"CombinedReduced": x.type() & y.type() & z.type()}
namespace = reduction(namespace)
print(namespace["CombinedReduced"])
#print(x.type().to(namespace))
