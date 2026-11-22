---
jupyter:
  jupytext:
    cell_markers: region,endregion
    formats: "ipynb,.pct.py:percent,.lgt.py:light,.spx.py:sphinx,md,Rmd,.pandoc.md:pandoc"
    text_representation:
      extension: .md
      format_name: pandoc
      format_version: 3.14
      jupytext_version: 1.20.1.dev0
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  nbformat: 4
  nbformat_minor: 2
---

::: {.cell .markdown}
# A quick insight at world population

## Collecting population data

In the below we retrieve population data from the
[World Bank](http://www.worldbank.org/)
using the [wbdata](https://github.com/OliverSherouse/wbdata) python package
:::

::: {.cell .code}
``` python
import pandas as pd
import wbdata as wb

pd.options.display.max_rows = 6
pd.options.display.max_columns = 20
```
:::

::: {.cell .markdown}
Corresponding indicator is found using search method - or, directly,
the World Bank site.
:::

::: {.cell .code}
``` python
wb.search_indicators('Population, total')  # SP.POP.TOTL
# wb.search_indicators('area')
# => https://data.worldbank.org/indicator is easier to use
```
:::

::: {.cell .markdown}
Now we download the population data
:::

::: {.cell .code}
``` python
indicators = {'SP.POP.TOTL': 'Population, total',
              'AG.SRF.TOTL.K2': 'Surface area (sq. km)',
              'AG.LND.TOTL.K2': 'Land area (sq. km)',
              'AG.LND.ARBL.ZS': 'Arable land (% of land area)'}
data = wb.get_dataframe(indicators, convert_date=True).sort_index()
data
```
:::

::: {.cell .markdown}
World is one of the countries
:::

::: {.cell .code}
``` python
data.loc['World']
```
:::

::: {.cell .markdown}
Can we classify over continents?
:::

::: {.cell .code}
``` python
data.loc[(slice(None), '2017-01-01'), :]['Population, total'].dropna(
).sort_values().tail(60).index.get_level_values('country')
```
:::

::: {.cell .markdown}
Extract zones manually (in order of increasing population)
:::

::: {.cell .code}
``` python
zones = ['North America', 'Middle East & North Africa',
         'Latin America & Caribbean', 'Europe & Central Asia',
         'Sub-Saharan Africa', 'South Asia',
         'East Asia & Pacific'][::-1]
```
:::

::: {.cell .markdown}
And extract population information (and check total is right)
:::

::: {.cell .code}
``` python
population = data.loc[zones]['Population, total'].swaplevel().unstack()
population = population[zones]
assert all(data.loc['World']['Population, total'] == population.sum(axis=1))
```
:::

::: {.cell .markdown}
## Stacked area plot with matplotlib
:::

::: {.cell .code}
``` python
import matplotlib.pyplot as plt
```
:::

::: {.cell .code}
``` python
plt.clf()
plt.figure(figsize=(10, 5), dpi=100)
plt.stackplot(population.index, population.values.T / 1e9)
plt.legend(population.columns, loc='upper left')
plt.ylabel('Population count (B)')
plt.show()
```
:::

::: {.cell .markdown}
## Stacked bar plot with plotly
:::

::: {.cell .code}
``` python
import plotly.offline as offline
import plotly.graph_objs as go

offline.init_notebook_mode()
```
:::

::: {.cell .code}
``` python
data = [go.Scatter(x=population.index, y=population[zone], name=zone, stackgroup='World')
        for zone in zones]
fig = go.Figure(data=data,
                layout=go.Layout(title='World population'))
offline.iplot(fig)
```
:::
