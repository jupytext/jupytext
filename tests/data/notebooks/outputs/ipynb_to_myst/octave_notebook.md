---
kernelspec:
  display_name: Octave
  language: octave
  name: octave
---

A markdown cell

```{code-cell}
1 + 1
```

```{code-cell}
% a code cell with comments
2 + 2
```

```{code-cell}
% a simple plot
x = -10:0.1:10;
plot (x, sin (x));
```

```{code-cell}
%plot -w 800
% a simple plot with a magic instruction
x = -10:0.1:10;
plot (x, sin (x));
```

And to finish with, a Python cell

```{code-cell} python
%%python
a = 1
```

```{code-cell} python
%%python
a + 1
```
