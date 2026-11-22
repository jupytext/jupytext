---
jupytext:
  formats: ipynb,.pct.py:percent,.lgt.py:light,.spx.py:sphinx,md,Rmd,.pandoc.md:pandoc,.myst.md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.20.1.dev0
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# A quick insight at world population

## Collecting population data

In the below we retrieve population data from the
[World Bank](http://www.worldbank.org/)
using the [wbdata](https://github.com/OliverSherouse/wbdata) python package

```{code-cell} ipython3
import pandas as pd
import wbdata as wb

pd.options.display.max_rows = 6
pd.options.display.max_columns = 20
```

Corresponding indicator is found using search method - or, directly,
the World Bank site.

```{code-cell} ipython3
wb.search_indicators('Population, total')  # SP.POP.TOTL
# wb.search_indicators('area')
# => https://data.worldbank.org/indicator is easier to use
```

Now we download the population data

```{code-cell} ipython3
indicators = {'SP.POP.TOTL': 'Population, total',
              'AG.SRF.TOTL.K2': 'Surface area (sq. km)',
              'AG.LND.TOTL.K2': 'Land area (sq. km)',
              'AG.LND.ARBL.ZS': 'Arable land (% of land area)'}
data = wb.get_dataframe(indicators, convert_date=True).sort_index()
data
```

World is one of the countries

```{code-cell} ipython3
data.loc['World']
```

Can we classify over continents?

```{code-cell} ipython3
data.loc[(slice(None), '2017-01-01'), :]['Population, total'].dropna(
).sort_values().tail(60).index.get_level_values('country')
```

Extract zones manually (in order of increasing population)

```{code-cell} ipython3
zones = ['North America', 'Middle East & North Africa',
         'Latin America & Caribbean', 'Europe & Central Asia',
         'Sub-Saharan Africa', 'South Asia',
         'East Asia & Pacific'][::-1]
```

And extract population information (and check total is right)

```{code-cell} ipython3
population = data.loc[zones]['Population, total'].swaplevel().unstack()
population = population[zones]
assert all(data.loc['World']['Population, total'] == population.sum(axis=1))
```

## Stacked area plot with matplotlib

```{code-cell} ipython3
import matplotlib.pyplot as plt
```

```{code-cell} ipython3
plt.clf()
plt.figure(figsize=(10, 5), dpi=100)
plt.stackplot(population.index, population.values.T / 1e9)
plt.legend(population.columns, loc='upper left')
plt.ylabel('Population count (B)')
plt.show()
```

## Stacked bar plot with plotly

+++

Stacked area plots (with cumulated values computed depending on
selected legends) are
[on their way](https://github.com/plotly/plotly.js/pull/2960) at Plotly. For
now we just do a stacked bar plot.

```{code-cell} ipython3
import plotly.offline as offline
import plotly.graph_objs as go

offline.init_notebook_mode()
```

```{code-cell} ipython3
bars = [go.Bar(x=population.index, y=population[zone], name=zone)
        for zone in zones]
fig = go.Figure(data=bars,
                layout=go.Layout(title='World population',
                                 barmode='stack'))
offline.iplot(fig)
```
