# %% [markdown]
# # Quarterly Sales
# A look at Q4 revenue by region.

# %%
import pandas as pd
df = pd.read_csv("sales.csv")

# %%
df.groupby("region")["revenue"].sum().plot.bar()
