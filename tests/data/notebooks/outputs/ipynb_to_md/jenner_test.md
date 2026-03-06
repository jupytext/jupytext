---
jupyter:
  kernelspec:
    display_name: Jenner
    language: jenner
    name: jenner
---

# Jenner Notebooks with Jupytext

```jenner
data test;
    x = 1;
    y = x * 2;
    output;
run;
```

```jenner
proc print data=test;
run;
```

```jenner
%let name = Jupytext;
%put &name;
```
