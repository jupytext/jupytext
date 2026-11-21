---
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

```{code-cell} html
%%html
<p><a href="https://github.com/mwouts/jupytext", style="color: rgb(0,0,255)">Jupytext</a> on GitHub</p>
```

```{code-cell} latex
%%latex
$\frac{\pi}{2}$
```

```{code-cell} ipython3
%load_ext rpy2.ipython
```

```{code-cell} R
%%R
library(ggplot2)
ggplot(data=data.frame(x=c('A', 'B'), y=c(5, 2)), aes(x,weight=y)) + geom_bar()
```

```{code-cell} ipython3
%matplotlib inline
import pandas as pd
pd.Series({'A':5, 'B':2}).plot(figsize=(3,2), kind='bar')
```
