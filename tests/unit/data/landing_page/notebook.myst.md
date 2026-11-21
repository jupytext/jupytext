# Quarterly Sales
A look at Q4 revenue by region.

```{code-cell}
import pandas as pd
df = pd.read_csv("sales.csv")
```

```{code-cell}
df.groupby("region")["revenue"].sum().plot.bar()
```
