# oneaway

Given a string ``s``, generate a bunch of potential typos for it, based on things like accidentally swapping letters, & common adjacency misses on a ``QWERTY`` keyboard layout.

## Rationale

I have _2_ potential needs for it at **dayjob** and I wrote this one evening before realising that it's basically mostly a poor facsimile of [``edits1(word)`` from "How to Write a Spelling Corrector"](https://norvig.com/spell-correct.html). Basically I need everything with a [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance) of **1**, or thereabouts.

Oh well 🤷

## Example usage

### As a CLI

```sh
> python -m oneaway "test"
```
gives us:
```markdown
# Variants allowed:
  - missing letters
  - swapped letters
  - horizonal typos
# Dictionary file `/usr/share/dict/words` being used:
  - yes
# Variations for `test`:
  - "est"
  - "tst" (clashes!)
  - "tet"
  - "etst"
  - "tset"
  - "tets"
  - "rest" (clashes!)
  - "yest" (clashes!)
  - "twst"
  - "trst"
  - "teat" (clashes!)
  - "tedt"
# Total: 12
# Variations which clash with known words: 4
  - "rest"
  - "teat"
  - "tst"
  - "yest"
# Variations as a (naïve) regular expression alternation:
  - (tset|tets|etst|twst|trst|teat|tedt|rest|yest|est|tst|tet)
```

### As a library

```python
>>> import oneaway
>>> results = oneaway.common("test")  # Returns a generator
>>> print(tuple(results))
(
    'est', 
    'tst', 
    'tet', 
    'etst', 
    'tset', 
    'tets', 
    'rest', 
    'yest', 
    'twst', 
    'trst', 
    'teat', 
    'tedt',
)
```

#### Library methods

##### ``dropped_letter(value)``

Generates variations on `value` where one of the letters is missing.

e.g. ``test`` → ``tst``

##### ``swapped_letter(value)``

Generates variations on `value` where the letters have been typed out-of-order.

e.g. ``ab`` has been swapped and appears as ``ba``

##### ``swapped_casing(value)``

Generates variations where one of the letters (and only one!) changed casing ... "accidentally" I guess?

Not super useful on it's own, because you're technically 2 keys away from doing it, so while it is an "edit distance" of 1 it's unlikely.

e.g. ``test`` → ``Test``

##### ``horizontal_proximity_typo(value)`` and ``vertical_proximity_typo(value)``

Based on a ``QWERTY`` keyboard, a single letter is substituted for one adjacent to it.

e.g. ``j`` can become ``h`` or ``k`` horizontally. It can become ``u``, ``i``, ``n``, or ``m`` vertically.

##### ``common(value)``

Generates variations based on ``dropped_letter``, ``swapped_letter``, and ``horizontal_proximity_typo``.

##### ``mix(value)``

Same as ``common`` above, but also includes ``vertical_proximity_typo``.