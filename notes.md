# From R to Python: DataFrames

## But First, the built-ins

Both languages have an extensive ecosystem of installable packages, but before we dive into those
let’s examine what’s available within the core of each language.

| **R (base)**      | **Python analogue**                      | **Notes**                              |
| ---------------   | ---------------------                    | ------------                           |
| list              | `list`                                   | Ordered, heterogeneous, nestable.      |
| named list        | `dict`                                   | Key–value pairs.                       |
| NULL              | `None`                                   | Absence of value.                      |
| NA                | `None`                                   | Missing/undefined data in a dataset.   |
| NaN               | `float('nan')`                           | Invalid float compuatation/numeric.    |
| atomic vector     | `polars.Series`*                         | Homogeneous values only.               |
| array             | `numpy.ndarray`                          | Multi-dimensional.                     |
| data.frame        | `polars.DataFrame`                       | Tabular data.                          |
| expression / call | `ast.AST`? Arbitrary strings?            | Unevaluated code.                      |
| S3 / S4 object    | `dataclass`, `class`, `namedtuple`       | Structured objects.                    |
| atomic units      | `int`, `float`, `bool`, `str`, etc.      | Scalars vs. R’s length-1 vectors.      |

**Scalars… and the lack thereof**

```python
print( 123 )
print([123])
```

```Rscript
  123
c(123)
```

**Basic Container Types**

```Rscript
list(123, 'hello')     # list      ; heterogeneous (can contain differently typed data)
list(a=123, b='hello') # named list; heterogeneous (can contain differently typed data)
c(123)                 # vector    ; homogenous (must contain singly typed data)
```

```python
from array import array

print(
    [123, 'hello'],           # list; heterogeneous (can contain differently typed data) 
    {'a': 123, 'b': 'hello'}, # dict; heterogeneous (can contain differently typed data) 
    array('i', [123, 456]),   # 1D-array; homogeneous (singly typed data; no one usually uses this in Python)
    sep='\n',
)
```

## The Basic DataFrame Structure

DataFrames across many languages are implemented as an ordered
*heterogeneous* collection of 1d *homogeneous* column-oriented vectors/arrays.

```Rscript
data <- data.frame(
    a=c(123, 456),
    b=c('hello', 'world'),
    c=c(TRUE, FALSE)
)

data
sapply(data, typeof)
```

```python
from polars import DataFrame

df = DataFrame({
    'a': [123, 456],
    'b': ['hello', 'world'],
    'c': [True, False],
})

print(
    # df,
    df.schema,
    sep='\n',
)
```

Columns themselves are 1d & homogeneous for decreased *memory* usage and increased *speed*
In Python we do not use the built-in data structures for this. Instead our array and data frame
libraries implement these structures from scratch in C/Rust.

*Memory*

```python
from sys import getsizeof
from itertools import repeat

from polars import Series

values = [*repeat(1, 100_000)]
series = Series(values)

print(
    f'{sum(getsizeof(x) for x in values) = : >10,}',
    f'{series.estimated_size()           = : >10,}',
    sep='\n',
)
```

```Rscript
xs_vec <- 1:1e6
xs_lst <- as.list(xs_vec)

object.size(xs_vec)
object.size(xs_lst)
```

And *speed*

```python
from sys import getsizeof
from itertools import repeat
from _utils import timed

from polars import Series

py_xs = [*repeat(1, 1_000_000)]
pl_xs = Series(py_xs)

with timed('Python list (comp)'):
    [x + 10 for x in py_xs]

with timed('Python list (map)'):
    [*map(lambda x: x + 10, py_xs)]

with timed('Polars Series'):
    pl_xs + 10
```

```Rscript
xs_vec <- 1:1000000
xs_lst <- as.list(xs_vec)

system.time(xs_vec + 10)
system.time(lapply(xs_lst, function(x) x + 10))
```

## Interacting (naively) with a DataFrame

This is not how we usually would interact with a Polars DataFrame, but one could…

```python
from polars import DataFrame

df = DataFrame({
    'a': [123, 456],
    'b': ['hello', 'world'],
    'c': [True, False],
})


print(
    df['a'],                    # select column 'a'
    df['a'] ** 2,               # select column 'a' and square it
    df['b'].str.to_uppercase(), # select column 'b' and uppercase all values
    sep='\n',
)
```

Similarly in R we can…

```Rscript
data <- data.frame(
    a=c(123, 456),
    b=c('hello', 'world'),
    c=c(TRUE, FALSE)
)

data$a          # select column a
data[['a']]     # select column a via a string
data$a ^ 2      # square column a
toupper(data$b) # upper case column b
```

But we typically don’t interact with DataFrames in either language in this manner.
One of the reasons is that the syntax becomes very repetitive

```Rscript
data <- data.frame(
    a=0:3,
    b=10:13,
    c=100:103,
    d=1000:1003
)

data$z <- data$a + (data$b * 2) + (data$c * 3) + (data$d * 4)
data

# Instead, we can use some of the *magic* of R
# suppressPackageStartupMessages({
#   library(dplyr)
# })
# data %>% mutate(z = a + (b*2) + (c*3) + (d*4))
```

Similarly in Python, we would…

```python
from polars import DataFrame, col

df = DataFrame({
    'a': range(4),
    'b': range(10, 14),
    'c': range(100, 104),
    'd': range(1000, 1004),
})

print(
    df.with_columns(
        z=df['a'] + (df['b'] * 2) + (df['c'] * 3) + (df['d'] * 4),
        # z=col('a') + (col('b') * 2) + (col('c') * 3) + (col('d') * 4),
    )
)
```

But in Python, it feels like we’re just swapping out repeating the variable name of the DataFrame
for some new repeated name. Is it just worse syntax?

## Expressing Yourself

As a feature of the language, R expressionss are lazily evaluated (read non-standard evaluation; NSE).

```Rscript
f <- function(expr) {
    100
}

f(x + y * 2) # no error!
```

Python, does not boast this feature.

```python
def f(expr):
    return 100

f(x + y * 2) # NameError: name 'x' is not defined
```

This feature in R allows for the separation of an expression from its evaluation
(in Python the expression is ALWAYS evaluated with the context of the available local/global variabbles)

```Rscript
f <- function(expr) {
    e <- substitute(expr)
    eval(e, list(x=10, y=20))
}

f(x + y * 2)
```

But is this feature always a good idea? It can make for some head scratching code.

```Rscript
f <- function(x, y = x + 1) {
    x <- y * 2
    y
}

f(10)
```

But since Python does not have this feature built into the language, the package Polars
invented an expression system of its own.

```python
from polars import col

print(
    col('a'),                    # column a
    col('a') ** 2,               # column a squared
    col('b').str.to_uppercase(), # column b as uppercased
    sep='\n',
)
```

## Expressions & DataFrames: a beautiful match

In R (dplyr) we have a grammer that lets us effectively compose expressions to operate on
data frames.

The following was taken from https://dplyr.tidyverse.org/
- `mutate()` adds new variables that are functions of existing variables
- `select()` picks variables based on their names.
- `filter()` picks cases based on their values.
- `summarise()` reduces multiple values down to a single summary.
- `arrange()` changes the ordering of the rows.

```Rscript
suppressPackageStartupMessages({
  library(dplyr)
})

data <- data.frame(
    a=0:3,
    b=10:13,
    c=100:103,
    d=1000:1003,
    group=c('g', 'g', 'h', 'h')
)

# data %>% mutate(z = a * 2)
# data %>% select(where(is.numeric))
# data %>% filter(a >= 2)
# data %>% summarise(mean(a), mean(b))
# data %>% group_by(group) %>% summarise(mean(a))
```

Here are the closest analogues for Python:
- `mutate()` → `DataFrame.select` (drops original columns) or `DataFrame.with_columns` (preserves original columns)
- `select()` → `polars.selectors` (a special type of expression)
- `filter()` → `DataFrame.filter`
- `summarise()` → `DataFrame.select` (the expressions are responsible for aggregating)
- `arrange()` → `DataFrame.sort`
- `group_by()` → `DataFrame.group_by`

Notice that all of the operations in Polars are attached to the DataFrame
object as methods that accept expressions.

```python
from polars import DataFrame, col
from polars import selectors as cs 

df = DataFrame({
    'a': range(4),
    'b': range(10, 14),
    'c': range(100, 104),
    'd': range(1000, 1004),
    'group': ['g', 'g', 'h', 'h'],
})

print(
    # df.with_columns(z=col('a') * 2),           # mutate(z = a * 2)
    # df.select(cs.numeric()),                   # select(a:c)
    # df.filter(col('a') >= 2),                  # filter(a >= 2)
    # df.select(col('a').mean()),                # summarise(mean(a), mean(b))
    # df.group_by('group').agg(col('a').mean()), # group_by(group) %>% summarise(mean(a))
    sep='\n',
)
```

In the above we see a few similarities and differences across both concepts and syntax.

Both R and Polars use delayed evaluation (in the form of expressions) to capture planned
execution. This lets us avoid modifying data in place, instead we build expressions that
describe transformations.

In the Polars model, expressions are evaluated within a particular context, where the *context* 
is the slice of data that the expression is evaluated against. When one uses `DataFrame.select`,
`DataFrame.with_columns`, or `DataFrame.filter` the evaluation context is the entire dataframe.
When one uses `DataFrame.group_by(…).agg(…)` the evaluation conttext is each individual group.

This provides a greate amount of flexibility to the expressions themselves. They dictate whether
or not we will aggregate or transform data.

```python
from polars import DataFrame, col
from polars import selectors as cs 

df = DataFrame({
    'a': range(4),
    'b': range(10, 14),
    'c': range(100, 104),
    'd': range(1000, 1004),
    'group': ['g', 'g', 'h', 'h'],
})

avg = col('a').mean()
print(
    df.select(avg),
    df.group_by('group').agg(avg)
)
```

## Let’s Solve some Problems

### Hows The Weather (Simple Problems)

```python
from io import StringIO

buffer = StringIO('''
      date  temperature  humidity  precipitation
2020-01-01           73       215           True
2020-01-02           77       217           True
2020-01-03           74       218          False
2020-01-04           NA       219          False
2020-01-05           78       220           True
2020-01-06           72       221          False
2020-01-07           90       209           True
2020-01-08           85       231           True
2020-01-09           84       211           True
'''.lstrip())

from pandas import read_csv as pd_read_csv
from polars import col, from_pandas, Date, Int64

df = (
    pd_read_csv(buffer, sep=r'\s{2,}', engine='python')
    .pipe(from_pandas)
    .cast({'temperature': Int64})
    .with_columns(
        col('date').str.strptime(Date, format='%Y-%m-%d')
    )
)
print(df)

# What is the weather on January 2nd?
# from datetime import date
# print(df.filter(col('date') == date(2020, 1, 2)))

# How many days did it rain? How many days did it not rain?
# print(df.select(col('precipitation').value_counts().struct.unnest()))

# What days were hotter than the preceding recorded day?
# from polars import duration
# print(
#     df.filter(col('temperature') > col('temperature').shift())
# )

# What was the hottest day when it rained?
# print(
#     df.filter(col('precipitation')).top_k(2, by='temperature')
# )

# What were the longest and shortest streaks of rainy days in a row; when did they begin?
# from polars import len
# print(
#     df.group_by(col('precipitation').rle_id())
#     .agg(
#         start=col('date').min(),
#         length=len(),
#         rained=col('precipitation').first()
#     )
#     .filter(col('rained'))
#     .drop('precipitation')
# )
```

### Credit Card Transactions (data cleaning problem)

```
transactions/
├── axpy
│   ├── 2020-01-01.csv
│   ├── 2020-01-02.csv
│   ├── 2020-01-03.csv
│   ├── 2020-01-04.csv
│   ...
├── credo.csv
└── finix.csv
```

```python
from pathlib import Path
from polars import scan_csv

transactions_dir = Path('data', 'transactions')

for p in ['credo.csv', 'finix.csv', 'axpy/2020-01-01.csv'][1:2]:
    print(p)
    print(scan_csv(transactions_dir / p).head(2).collect())

# date, merchant, category, transaction_date, type, amount
# dt  , str     , cat     , dt              , enum, float
```

```python
from polars import scan_csv, col, Enum, Date, Categorical, Int8, Float64

SpendType = Enum(['purchase', 'refund'])

## Axpy
axpy_df = (
    scan_csv('data/transactions/axpy/*.csv', include_file_paths='path')
    .rename(str.lower)
    .with_columns(
        date=col('path').str.strptime(Date(), format='data/transactions/axpy/%Y-%m-%d.csv'),
    )
    .cast({'category': Categorical, 'type': SpendType})
    .drop('path')
)

## Finix
finix_df = (
    scan_csv('data/transactions/finix.csv')
    .rename({'store': 'merchant'})
    .with_columns(
        col('date').str.strptime(Date(), format='%m/%d/%Y'),
        col('amount').abs(),
        type=col('amount').lt(0).cast(Int8).cast(SpendType),
    )
    .cast({'category': Categorical})
)



## Credo
credo_df = (
    scan_csv('data/transactions/credo.csv')
    .rename(str.lower)
    .with_columns(
        date=col('transaction_date').str.strptime(Date(), format='%Y-%m-%d'),
    )
    .unpivot(
        on=['purchase', 'refund'],
        index=['merchant', 'category', 'date'],
        variable_name='type',
        value_name='amount'
    )
    .filter(col('amount').is_not_null())
    .cast({'type': SpendType, 'category': Categorical, 'amount': Float64})
)

from polars import concat, lit
dfs = {
    'axpy': axpy_df,
    'finix': finix_df,
    'credo': credo_df,
}

result = concat([df.with_columns(source=lit(name)) for name, df in dfs.items()], how='diagonal')
result.sink_parquet('data/transactions/clean.parquet')

print(result.head().collect())
print('done!')
```

```python
from polars import scan_parquet, col

print(
    scan_parquet('data/transactions/clean.parquet')
    .group_by(['source', 'type']).agg(
        col('amount').sum(),
        start_date=col('date').min(),
        end_date=col('date').max(),
    )
    .sort('source', 'type')
    .collect()
)
```

## Wrap Up
