---
kernelspec:
  display_name: Jenner
  language: jenner
  name: jenner
---

# Jenner Notebooks with Jupytext

```{code-cell}
data test;
    x = 1;
    y = x * 2;
    output;
run;
```

```{code-cell}
proc print data=test;
run;
```

```{code-cell}
%let name = Jupytext;
%put &name;
```
