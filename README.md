# MoreSets
an extremely small collection of extra set classes.

This file provides
  - `OrderedSet` I did not invent this, but I did implement methods that make it seem native.
  - `DoubleSidedSet` This is something like a double ended vector. It appends to the furthest left, and pops off the furthest right.
  - `ExhaustiveSet` This takes the same idea as the double sided set, except limits the amount of elements it holds, popping off the oldest elements if it exceeds its max compacity.
