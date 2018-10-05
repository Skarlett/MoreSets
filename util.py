
import copy
from weakref import proxy, ReferenceError
import sys

if sys.version_info[0] == 3:
    # Avoid depreciation warning
    import collections.abc
    baseclass = collections.abc.MutableSet

else:
    import collections
    baseclass = collections.MutableSet


class Link(object):
    __slots__ = 'prev', 'next', 'key', '__weakref__'

class OrderedSet(baseclass):
    'Set that remembers the order of the elements that were added'
    # Source: https://github.com/ActiveState/code/blob/3b27230f418b714bc9a0f897cb8ea189c3515e99/recipes/Python/576696_OrderedSet_with_Weakrefs/recipe-576696.py
    # Big-O running times for all methods are the same as for regular sets.
    # The internal self._map dictionary maps keys to links in a doubly linked list.
    # The circular doubly linked list starts and ends with a sentinel element.
    # The sentinel element never gets deleted (this simplifies the algorithm).
    # The prev/next links are weakref proxies (to prevent circular references).
    # Individual links are kept alive by the hard reference in self._map.
    # Those hard references disappear when a key is deleted from an OrderedSet.

    def __init__(self, iterable=None):
        self._root = root = Link()         # sentinel node for doubly linked list
        root.prev = root.next = root
        self._map = {}                     # key --> link
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self._map)

    def __contains__(self, key):
        return key in self._map

    def __iter__(self):
        # Traverse the linked list in order.
        root = self._root
        curr = root.next
        while curr is not root:
            yield curr.key
            try:
              curr = curr.next
            except ReferenceError:
              raise RuntimeError("Was modified during iteration")

    def __reversed__(self):
        # Traverse the linked list in reverse order.
        root = self._root
        curr = root.prev
        while curr is not root:
          yield curr.key
          curr = curr.prev

    def copy(self):
      return copy.copy(self)

    def union(self, *others):
      instance = self.__class__()
      instance.update(*others)
      return instance

    def issuperset(self, other):
        return all(x in self for x in other)

    def issubset(self, other):
        return all(x in other for x in self)

    def update(self, *other):
        for iter in other:
            assert hasattr(iter, '__iter__')
            for x in iter:
                self.add(x)

    def difference(self, *other):
        instance = self.__class__()
        for iter in other:
          assert hasattr(iter, '__contains__')
          for v in self:
              if not v in iter:
                  instance.add(v)
        return instance

    def difference_update(self, other):
        assert hasattr(other, '__iter__')
        for v in other:
          if v in self:
            self.discard(v)

    def intersection(self, *other):
        instance = self.__class__()
        for iter in other:
            assert hasattr(iter, "__iter__")
            for seg in iter:
                if seg in self:
                    instance.add(seg)
        return instance

    def intersection_update(self, *other):
        discarded = []
        for p in self:
          for iter in other:
            if not p in iter:
              discarded.append(p)

        for x in discarded:
          self.discard(x)

    def symmetric_difference(self, other):
        instance = self.__class__()
        for x in self:
          if not x in other:
            instance.add(x)

        for x in instance:
            if not x in other:
                instance.add(x)
        return instance

    def symmetric_difference_update(self, other):
        discarded = []
        for x in self:
          if x in other:
            discarded.append(x)

        for x in other:
          if not x in self:
            self.add(x)

        for x in discarded:
          self.discard(x)

    def add(self, key):
        # Store new key in a new link at the end of the linked list
        if key not in self._map:
            self._map[key] = link = Link()
            root = self._root
            last = root.prev
            link.prev, link.next, link.key = last, root, key
            last.next = root.prev = proxy(link)
            return True
        return False

    def discard(self, key):
        # Remove an existing item using self._map to find the link which is
        # then removed by updating the links in the predecessor and successors.
        if key in self._map:
            link = self._map.pop(key)
            link.prev.next = link.next
            link.next.prev = link.prev

    def remove(self, element):
        self.discard(element)

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = next(reversed(self)) if last else next(iter(self))
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return not self.isdisjoint(other)


class DoubleSidedSet(OrderedSet):
  '''Set that remembers order, pops from the furthermost right, and appends to the most left '''
  def add(self, key):
    if key not in self._map:
      self._map[key] = link = Link()
      root = self._root
      last = root.next
      link.next, link.prev, link.key = last, root, key
      last.prev = root.next = proxy(link)
      return True
    return False


class ExhaustiveSet(DoubleSidedSet):
  ''' Set that automatically deletes oldest entries if exceeds limit '''
  def __init__(self, iterable=None, limit=1000, garbage_hook=None):
    self.limit = limit
    self.garbage_collector = garbage_hook
    DoubleSidedSet.__init__(self, iterable)

  def add(self, key):
    if DoubleSidedSet.add(self, key) and len(self) >= self.limit:
      if self.garbage_collector:
        for _ in range(len(self) - self.limit):
          self.garbage_collector(self.pop())
      else:
        for _ in range(len(self) - self.limit):
          self.pop()
      return True
    return False

class _UnitTest:
  ''' Lets assert these work like we imagine '''

  @staticmethod
  def test_create(iterable):
    return len(iterable(range(100))) == 100

  @staticmethod
  def test_pops_from_bottom(iterable):
    return iterable(range(5)).pop() == 0

  @staticmethod
  def test_adds_to_top(iterable):
    return list(iterable(range(5)))[0] == 4

  @staticmethod
  def test_reverse(iterable):
    instance = iterable(range(5))
    return list(instance)[0] != list(reversed(instance))[0]

  @staticmethod
  def test_pop(iterable):
    instance = iterable(range(100))
    for _ in range(len(instance)):
      instance.pop()
    return True

  @staticmethod
  def test_exhaustive(iterable):
      instance = iterable(range(10000))
      if hasattr(instance, "limit"):
        return len(instance) == instance.limit
      return False

  @staticmethod
  def test_delete(iterable):
    instance = iterable(range(5))
    i = instance.pop()
    return i not in instance

  @staticmethod
  def test_method_coverage(iterable):
    methods = dir(set)
    for x in methods:
      if not hasattr(iterable, x):
        print("[WARNING] {} doesn\'t support {}".format(iterable.__name__, x))
    return all(hasattr(iterable, method) for method in methods)

  @staticmethod
  def test_method_behavior(iterable):

    tests = []

    for method in dir(iterable):
      bench = set(range(100))
      instance = iterable(range(100))
      if not method.startswith("_") and not method in ['add', 'pop', 'clear', 'copy', 'discard', 'remove']:

          bench_test = getattr(bench, method)(range(25))
          ours = getattr(instance, method)(range(25))
          success = False
          try:
              if bench_test == ours:
                  success = True
              elif list(bench_test) == list(ours):
                  success = True
          except:
              print("FAILED METHOD: {} | {} {}".format(method, bench_test, ours))
              success = False

          print("{} | {} -> {} ".format(iterable.__name__, method, success))
          if success == False:
              print('FAILED METHOD ({}): {} {}'.format(method, bench_test, ours))
          tests.append(success)
    return all(tests)


  @classmethod
  def test(cls, classes):
    tests = tuple((getattr(cls, x), x.split('_', 1)[1]) for x in dir(cls) if x.startswith('test_'))

    for icls in classes:
      print("-"*20)
      print(icls.__name__)
      for test, name in tests:
        try:
          resp = test(icls)
        except Exception as e:
          resp = e
        print("{} | {} -> {}".format(icls.__name__, name, resp))

if __name__ == "__main__":
  _UnitTest.test([OrderedSet, DoubleSidedSet, ExhaustiveSet])
