TAB = "  "


class AbstractUnion:
    def __init__(self):
        self.options = list()

    def _describe(self, tab=0):
        options = {t._describe(): t for t in self.options}
        if len(options) == 0:
            return "\n"+TAB*tab+"any\n"
        if len(options) == 1:
            return list(options.values())[0]._describe(tab)
        #ret = "\n"+TAB*tab+"union:"
        ret = ""
        #tab += 1
        for t in options.values():
            ret += "\n"+TAB*tab+"- "+t._describe(tab+1)[len(TAB*(tab+1)):]
        return ret

    def __str__(self):
        return self._describe(0)

    def __eq__(self, other):
        if not isinstance(other, AbstractUnion):
            return len(self.options) == 1 and self.options[0] == other
        if len(self.options) != len(other.options):
            return False
        for opt1, opt2 in zip(self.options, other.options):
            if opt1 != opt2:
                return False
        return True

    def __ge__(self, other):
        return other.__le__(self)

    def __le__(self, other):
        if len(self.options) == 0:
            return True
        if not isinstance(other, AbstractUnion):
            return len(self.options) == 1 and self.options[0] <= other
        buckets1 = dict()
        buckets2 = dict()
        for t in self.options:
            num = t.num_nodes()
            if num not in buckets1:
                buckets1[num] = list()
            buckets1[num].append(t)
        for t in other.options:
            num = t.num_nodes()
            if num not in buckets2:
                buckets2[num] = list()
            buckets2[num].append(t)
        for num in buckets1:
            if num not in buckets2:
                return False
        for num in buckets1:
            list1 = buckets1[num]
            list2 = buckets2[num]
            # TODO: check that indeed this is not approximate
            for t1 in list1:
                exists = False
                for t2 in list2:
                    if t1 <= t2:
                        exists = True
                        break
                if not exists:
                    return False
        return True

    def num_nodes(self):
        return len(self.options)

    def __and__(self, other):
        ret = AbstractUnion()
        ret.options.extend(self.options)
        if isinstance(other, AbstractUnion):
            for t2 in other.options:
                found = False
                for t1 in self.options:
                    if t1 <= t2:
                        found = True
                        break
                if not found:
                    ret.options.append(t2)
        else:
            found = False
            for t1 in self.options:
                if t1 <= other:
                    found = True
                    break
            if not found:
                ret.options.append(other)

        l1 = 1
        while l1 < len(ret.options):
            l2 = l1-1
            while l2 >= 0:
                t1 = ret.options[l1]
                t2 = ret.options[l2]
                if t1 <= t2:
                    ret.options.remove(t1)
                    l1 -= 1
                    break
                l2 -= 1
            l1 += 1
            if l1 >= len(ret.options):
                break
        return ret

    def __contains__(self, obj):
        for t in self.options:
            if obj in t:
                return True
        return False


class AbstractValue:
    def __init__(self, class_name):
        self.class_name = class_name

    def _describe(self, tab=0):
        return "\n"+TAB*tab+"class: "+self.class_name

    def __str__(self):
        return self._describe(0)

    def __eq__(self, other):
        if isinstance(other, AbstractUnion):
            return len(other.options) == 1 and self == other.options[0]
        if not isinstance(other, AbstractValue):
            return False
        return self.class_name == other.class_name

    def __ge__(self, other):
        return other.__le__(self)

    def __le__(self, other):
        if isinstance(other, AbstractUnion):
            for t in other.options:
                if self <= t:
                    return True
            return False
        if not isinstance(other, AbstractValue) and not isinstance(other, AbstractObject):
            return False
        if self.class_name is None:
            return True
        return self.class_name == other.class_name

    def num_nodes(self):
        return 1

    def __and__(self, other):
        if isinstance(other, AbstractValue):
            if self.class_name is None:
                return AbstractValue(other.class_name)
            if other.class_name is None:
                return self
        ret = AbstractUnion()
        ret.options.append(self)
        ret.options.append(other)
        return ret

    def __contains__(self, obj):
        return obj.__class__.__name__ == self.class_name


class AbstractObject:
    def __init__(self):
        self.class_name = None
        self.members = dict()
        self.returns = AbstractUnion()

    def _describe(self, tab=0):
        ret = ""
        if tab == 0:
            ret += "object:"
            tab += 1
        if self.class_name is not None:
            ret += "\n" + TAB * tab + "class: " + self.class_name
        for member in self.members:
            ret += "\n"+TAB*tab+member+": "+self.members[member]._describe(tab+1)
        if len(self.returns.options) > 0:
            ret += "\n"+TAB*tab+"returns:"+self.returns._describe(tab+1)
        return ret

    def __str__(self):
        return self._describe(0)

    def __eq__(self, other):
        if isinstance(other, AbstractUnion):
            return len(other.options) == 1 and self == other.options[0]
        if isinstance(other, AbstractValue):
            if self.class_name is None or other.class_name is None:
                return False
            return self.class_name == other.class_name
        if not isinstance(other, AbstractObject):
            return False
        if self.returns != other.returns:
            return False
        if len(self.members) != len(other.members):
            return False
        for member in self.members:
            if member not in other.members:
                return False
            if self.members[member] != other.members[member]:
                return False
        for member in other.members:
            if member not in self.members:
                return False
            if self.members[member] != other.members[member]:
                return False
        if (self.class_name is None) != (other.class_name is None):
            return False
        return (self.class_name is None) or (self.class_name == other.class_name)

    def __ge__(self, other):
        return other.__le__(self)

    def __le__(self, other):
        if isinstance(other, AbstractUnion):
            for t in other.options:
                if self <= t:
                    return True
            return False
        if isinstance(other, AbstractValue):
            if self.class_name is None or other.class_name is None:
                return False
            return self.class_name == other.class_name
        if not isinstance(other, AbstractObject):
            return False
        if not (self.returns <= other.returns):
            return False
        if not (len(self.members) <= len(other.members)):
            return False
        for member in self.members:
            if member not in other.members:
                return False
            if not (self.members[member] <= other.members[member]):
                return False
        if self.class_name is None:
            return True
        if other.class_name is None:
            return False
        return self.class_name == other.class_name

    def num_nodes(self):
        ret = 1
        for child in self.members.values():
            ret += child.num_nodes()
        for child in self.returns.options:
            ret += child.num_nodes()
        return ret

    def __getitem__(self, item):
        return self.members[item]

    def __and__(self, other):
        if isinstance(other, AbstractObject):
            ret = AbstractObject()
            for member in self.members:
                ret.members[member] = self.members[member]
            for member in other.members:
                if member not in ret.members:
                    ret.members[member] = other.members[member]
                else:
                    ret.members[member] = ret.members[member] & other.members[member]
            ret.returns = self.returns & other.returns
            return ret
        ret = AbstractUnion()
        ret.options.append(self)
        ret.options.append(other)
        return ret

    def __contains__(self, obj):
        for member in self.members:
            if not hasattr(obj, member):
                return False
            if getattr(obj, member) not in self.members[member]:
                return False
        #if not callable(obj) and len(self.returns.options) > 0:
        #    return False
        return True

    def to(self, namespace):
        from duckstruct.reduction import convert
        return convert(self, namespace)
