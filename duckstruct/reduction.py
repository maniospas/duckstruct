from duckstruct.abstract import AbstractObject, AbstractUnion, AbstractValue


def reduction(namespace, shrink=False):
    global __abstract_typesearch_reduction_changes
    while True:
        __abstract_typesearch_reduction_changes = 0
        prev_namespace = namespace
        namespace = {k: _detection(v, namespace) for k, v in namespace.items()}
        for k, v in namespace.items():
            if isinstance(v, AbstractValue):
                __abstract_typesearch_reduction_changes -= 1
                namespace[k] = prev_namespace[k]
        if __abstract_typesearch_reduction_changes == 0:
            break
    if shrink:
        namespace = _shrink(namespace)
    return namespace


def convert(t, namespace):
    global __abstract_typesearch_reduction_changes
    while True:
        __abstract_typesearch_reduction_changes = 0
        prev_t = t
        t = _detection(t, namespace)
        if isinstance(t, AbstractValue):
            return prev_t
        if __abstract_typesearch_reduction_changes == 0:
            break
    return t


def _shrink(namespace):
    namespace = {k: v for k, v in namespace.items()}
    while True:
        changed = False
        for k, v in namespace.items():
            found = False
            for k2, v2 in namespace.items():
                if id(k) != id(k2) and k <= k2:
                    found = True
                    break
            if found:
                del namespace[k]
                changed = True
                break
        if not changed:
            break
    return namespace

def _detection(t, namespace):
    if isinstance(t, AbstractObject):
        candidates = [AbstractValue(k) for k, v in namespace.items() if id(t) != id(v) and t <= v]
        if candidates:
            global __abstract_typesearch_reduction_changes
            __abstract_typesearch_reduction_changes += 1  # TODO: fix this to be non-global (everything in a class)
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            ret = AbstractUnion()
            ret.options = candidates
            return ret

    if isinstance(t, AbstractObject):
        ret = AbstractObject()
        ret.class_name = t.class_name
        for k, v in namespace.items():
            if t <= v:
                ret.class_name = k
        for k, v in t.members.items():
            ret.members[k] = _detection(v, namespace)
        ret.returns = _detection(t.returns, namespace)
        return ret

    if isinstance(t, AbstractUnion):
        ret = AbstractUnion()
        for option in t.options:
            ret.options.append(_detection(option, namespace))
        return ret

    if isinstance(t, AbstractValue):
        return AbstractValue(t.class_name)

    raise Exception("Invalid type")