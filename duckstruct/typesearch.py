from duckstruct import abstract
from duckstruct.abstract import TAB


def get_hash(obj):
    try:
        return hash(obj)
    except:
        return id(obj)


class Union:
    def __init__(self, *args):
        self.types = list()
        for arg in args:
            self.add(arg)

    def add(self, value):
        if not isinstance(value, Type):
            raise Exception()
        self.types.append(value)

    def abstract(self):
        ret = abstract.AbstractUnion()
        for t in self.types:
            ret.options.append(t.abstract())
        return ret

    def describe(self, tab=0):
        types = {t.describe(): t for t in self.types}
        if len(types) == 0:
            return TAB*tab+"any\n"
        if len(types) == 1:
            return list(types.values())[0].describe(tab)
        ret = TAB*tab+"union:\n"
        tab += 1
        for t in types.values():
            ret += TAB*tab+"- "+t.describe(tab+1)[len(TAB*(tab+1)):]+"\n"
        return ret[:-1]


class Type:
    def __init__(self, value, assigned=False):
        self.value = value
        self.assigned = assigned
        #self.return_type = None #Union() if (isinstance(value, TypeListener) and callable(value._typesearch_wrapped_obj)) else None

    def describe(self, tab=0):
        value = self.value._typesearch_describe(tab) if isinstance(self.value, TypeListener) else ""
        ret = value+"\n" if value else TAB*tab+"class: "+str(self.value.__class__.__name__)+"\n"
        while ret[-1] == "\n":
            ret = ret[:-1]
        return ret

    def abstract(self):
        if isinstance(self.value, TypeListener):
            desc = self.value._typesearch_attributes.describe()
            if desc != "object:\n":
                return self.value._typesearch_attributes.abstract()
            return abstract.AbstractValue(self.value._typesearch_wrapped_obj.__class__.__name__)
        return abstract.AbstractValue(str(self.value.__class__.__name__))


class ObjectType:
    def __init__(self):
        self.dict = dict()
        self.returns = None

    def __contains__(self, item):
        return item in self.dict

    def __str__(self):
        return self.describe()

    def __setitem__(self, key, value):
        self.dict[key] = value

    def __getitem__(self, key):
        return self.dict[key]

    def describe(self, tab=0):
        if tab == 0:
            ret = TAB*tab+"object:\n"
            tab += 1
        else:
            ret = ""
        for key, value in self.dict.items():
            ret += TAB*tab+key+":\n"+value.describe(tab+1)+"\n"
        while ret and ret[-1] == "\n":
            ret = ret[:-1]
        if tab == 1:
            ret += "\n"
        if self.returns is not None:
            ret += TAB*tab+"returns:\n"+self.returns.describe(tab+1)
        return ret

    def abstract(self):
        ret = abstract.AbstractObject()
        for t in self.dict:
            ret.members[t] = self.dict[t].abstract()
        if self.returns is not None:
            for t in self.returns.types:
                ret.returns.options.append(t.abstract())
        return ret



_method_depth = dict()


class TypeListener(object):
    def __init__(self, obj=None, parent=None):
        self._typesearch_wrapped_obj = obj
        self._typesearch_attributes = ObjectType()
        self._typesearch_wraps = dict()
        self._typesearch_attributes.returns = None
        self._typesearch_parent = parent
        self.type = lambda: self._typesearch_attributes.abstract()

        def describe(tab):
            desc = self._typesearch_attributes.describe(tab)
            if desc != TAB*tab+"object:\n" and desc:
                return desc
            return TAB * tab + "class: "+self._typesearch_wrapped_obj.__class__.__name__
        self._typesearch_describe = describe

        """if isinstance(self._typesearch_wrapped_obj, object) and hasattr(self._typesearch_wrapped_obj, "__dict__"):
            for attr in self._typesearch_wrapped_obj.__dict__:
                self._typesearch_attributes[attr] = Type(self._typesearch_wrapped_obj.__dict__[attr])"""

    def __setattr__(self, attr, obj):
        if attr in ('_typesearch_wrapped_obj', '_typesearch_attributes', '_typesearch_wraps', 'type',
                    '_typesearch_describe', '_typesearch_returns', '_typesearch_parent'):
            return super().__setattr__(attr, obj)
        """if attr in self._typesearch_attributes:
            if isinstance(self._typesearch_attributes[attr], Union):
                self._typesearch_attributes[attr].add(Type(obj, assigned=True))
            else:
                self._typesearch_attributes[attr] = Union(self._typesearch_attributes[attr], Type(obj, assigned=True))
        else:
            self._typesearch_attributes[attr] = Type(obj, assigned=True)"""
        return setattr(self._typesearch_wrapped_obj, attr, obj)

    def __getattr__(self, attr):
        if attr in ('_typesearch_wrapped_obj', '_typesearch_attributes', '_typesearch_wraps', 'type',
                    '_typesearch_describe', '_typesearch_returns', '_typesearch_parent'):
            return getattr(self, attr)
        obj = getattr(self._typesearch_wrapped_obj, attr)

        if not isinstance(obj, TypeListener):
            if get_hash(obj) in self._typesearch_wraps:
                obj = self._typesearch_wraps[get_hash(obj)]
            else:
                base_obj = obj
                obj = TypeListener(obj, self)
                self._typesearch_wraps[get_hash(base_obj)] = obj

        if _method_depth.get(id(self._typesearch_parent), 0) <= 1:
            if attr in self._typesearch_attributes:
                if isinstance(self._typesearch_attributes[attr], Union):
                    self._typesearch_attributes[attr].add(Type(obj))
                else:
                    self._typesearch_attributes[attr] = Union(self._typesearch_attributes[attr], Type(obj))
            else:
                self._typesearch_attributes[attr] = Type(obj)
        return obj

    def __call__(self, *args, _recursive_type=False, **kwargs):
        global _method_depth
        if id(self._typesearch_parent) not in _method_depth:
            _method_depth[id(self._typesearch_parent)] = 1
        else:
            _method_depth[id(self._typesearch_parent)] += 1
        ret = self._typesearch_wrapped_obj(*args, **kwargs)
        if _recursive_type:
            ret = TypeListener(ret)
        _method_depth[id(self._typesearch_parent)] -= 1
        if _method_depth[id(self._typesearch_parent)] == 0:
            if self._typesearch_attributes.returns is None:
                self._typesearch_attributes.returns = Union()
            self._typesearch_attributes.returns.add(Type(ret))
            del _method_depth[id(self._typesearch_parent)]
        return ret

    def __add__(self, *args, **kwargs):
        attr = "__add__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __sub__(self, *args, **kwargs):
        attr = "__sub__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __mul__(self, *args, **kwargs):
        attr = "__mul__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __mod__(self, *args, **kwargs):
        attr = "__mod__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __float__(self, *args, **kwargs):
        attr = "__float__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __bool__(self, *args, **kwargs):
        attr = "__bool__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __int__(self, *args, **kwargs):
        attr = "__int__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __len__(self, *args, **kwargs):
        attr = "__len__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __divmod__(self, *args, **kwargs):
        attr = "__divmod__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __neg__(self, *args, **kwargs):
        attr = "__neg__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __ge__(self, *args, **kwargs):
        attr = "__ge__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __le__(self, *args, **kwargs):
        attr = "__le__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __gt__(self, *args, **kwargs):
        attr = "__gt__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __lt__(self, *args, **kwargs):
        attr = "__lt__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __eq__(self, *args, **kwargs):
        attr = "__eq__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __and__(self, *args, **kwargs):
        attr = "__and__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __or__(self, *args, **kwargs):
        attr = "__or__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __xor__(self, *args, **kwargs):
        attr = "__xor__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __invert__(self, *args, **kwargs):
        attr = "__invert__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __abs__(self, *args, **kwargs):
        attr = "__abs__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __enter__(self, *args, **kwargs):
        attr = "__enter__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __exit__(self, *args, **kwargs):
        attr = "__exit__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __contains__(self, *args, **kwargs):
        attr = "__contains__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __iter__(self, *args, **kwargs):
        attr = "__iter__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __getitem__(self, *args, **kwargs):
        attr = "__getitem__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __setitem__(self, *args, **kwargs):
        attr = "__setitem__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __rshift__(self, *args, **kwargs):
        attr = "__rshift__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __lshift__(self, *args, **kwargs):
        attr = "__lshift__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __long__(self, *args, **kwargs):
        attr = "__long__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __index__(self, *args, **kwargs):
        attr = "__index__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __hex__(self, *args, **kwargs):
        attr = "__hex__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __bytes__(self, *args, **kwargs):
        attr = "__bytes__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __aiter__(self, *args, **kwargs):
        attr = "__alter__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __aenter__(self, *args, **kwargs):
        attr = "__aenter__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __aexit__(self, *args, **kwargs):
        attr = "__aexit__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __anext__(self, *args, **kwargs):
        attr = "__anext__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __next__(self, *args, **kwargs):
        attr = "__next__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __idiv__(self, *args, **kwargs):
        attr = "__idiv__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __floor__(self, *args, **kwargs):
        attr = "__floor__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __ceil__(self, *args, **kwargs):
        attr = "__ceil__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __floordiv__(self, *args, **kwargs):
        attr = "__floordiv__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __complex__(self, *args, **kwargs):
        attr = "__complex__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, **kwargs)
        return ret

    def __iadd__(self, *args, **kwargs):
        attr = "__iadd__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __isub__(self, *args, **kwargs):
        attr = "__isub__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __imul__(self, *args, **kwargs):
        attr = "__imul__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __imod__(self, *args, **kwargs):
        attr = "__imod__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __truediv__(self, *args, **kwargs):
        attr = "__truediv__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __rdiv__(self, *args, **kwargs):
        attr = "__rdiv__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __radd__(self, *args, **kwargs):
        attr = "__radd__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __rsub__(self, *args, **kwargs):
        attr = "__rsub__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __rmul__(self, *args, **kwargs):
        attr = "__rmul__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __pow__(self, *args, **kwargs):
        attr = "__pow__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __rpow__(self, *args, **kwargs):
        attr = "__rpow__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret

    def __ipow__(self, *args, **kwargs):
        attr = "__ipow__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method(*args, _recursive_type=True, **kwargs)
        return ret



    def __repr__(self):
        attr = "__repr__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method()
        return ret

    def __str__(self):
        attr = "__str__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method()
        return ret

    def __hash__(self):
        attr = "__hash__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method()
        return ret

    def __nonzero__(self):
        attr = "__nonzero__"
        method = getattr(self._typesearch_wrapped_obj, attr)
        if attr not in self._typesearch_wraps:
            self._typesearch_wraps[method] = TypeListener(method, self)
            self._typesearch_attributes[attr] = Type(self._typesearch_wraps[method])
        method = self._typesearch_wraps[method]
        ret = method()
        return ret
