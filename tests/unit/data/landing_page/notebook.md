# Quarterly Sales
A look at Q4 revenue by region.

```python
import pandas as pd
df = pd.read_csv("sales.csv")
```

```python
df.groupby("region")["revenue"].sum().plot.bar()
```
