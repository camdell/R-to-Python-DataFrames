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
# 123
c(123, 456)
```

**Basic Container Types**

```Rscript
# list(123L, 'hello')     # list      ; heterogeneous (can contain differently typed data)
x <- list(a=123, b='hello') # named list; heterogeneous (can contain differently typed data)
x[['a']]
# c(123L)                 # vector    ; homogenous (must contain singly typed data)
```

```python
from array import array

# x = [123, 'hello']           # list; heterogeneous (can contain differently typed data) 
# print(x[0])

# x = {'a': 123, 'b': 'hello', 0: 'world'} # dict; heterogeneous (can contain differently typed data) 
# print(x['a'])
# print(x)

print(
    array('i', [123, 456]),   # 1D-array; homogeneous (singly typed data; no one usually uses this in Python)
    sep='\n',
)
```

## The Basic DataFrame Structure

DataFrames across many languages are implemented as an ordered
*heterogeneous* collection of 1d *homogeneous* column-oriented vectors/arrays.

as a list of vectors.

```Rscript
list(a=c(123, 456))
```

```Rscript
data <- data.frame(
    a=c(123, 456),
    b=c('hello', 'world'),
    c=c(TRUE, FALSE)
)

data_list <- list(
    a=c(123, 456),
    b=c('hello', 'world'),
    c=c(TRUE, FALSE)
)

sapply(data, typeof)
lapply(data_list, typeof)
```

1. pandas (OG) originated in 2010
2. Polars (2nd generation of DataFrames in Python)
3. DuckDB (2nd generation DataFrame)

```python
from polars import DataFrame

df = DataFrame({
    'a': [123, 456],
    'b': ['hello', 'world'],
    'c': [True, False],
})

# print(df)
print(df.glimpse())
print(glimpse(df))
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
    f'{sum(getsizeof(x) for x in values) = : >10,}', # Python list
    f'{series.estimated_size()           = : >10,}', # Polars Series
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

print(df)

print(
    # df['a'],                    # select column 'a'
    # df['a'] ** 2,               # select column 'a' and square it
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

# data$a          # select column a
# data[['a']]     # select column a via a string
# data$a ^ 2      # square column a
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
library(dplyr, warn.conflicts = FALSE)
data %>% mutate(z = a + (b*2) + (c*3) + (d*4))
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
        # z=df['a'] + (df['b'] * 2) + (df['c'] * 3) + (df['d'] * 4),
        z=col('a') + (col('b') * 2) + (col('c') * 3) + (col('d') * 4),
    )
)
```

But in Python, it feels like we’re just swapping out repeating the variable name of the DataFrame
for some new repeated name. Is it just worse syntax?

## Expressing Yourself

As a feature of the language, R expressionss are lazily evaluated (read non-standard evaluation; NSE).

```Rscript
f <- function(expr) {
    expr
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
    eval(e, list(x=100, y=20))
}

f(x + y * 2)
```

But is this feature always a good idea? It can make for some head scratching code.

```Rscript
f <- function(x, y = x + 1) {
    # x is 10
    x <- y * 2
    # x is 22
    y # 22 + 1
}

f(10)
```

But since Python does not have this feature built into the language, the package Polars
invented an expression system of its own.

```python
from polars import col

print(
    # col('a'),                    # column a
    # col('a') ** 2,               # column a squared
    # col('b').str.to_uppercase(), # column b as uppercased
    sep='\n',
)
```

## Expressions & DataFrames: a beautiful match

In R (dplyr) we have a grammar that lets us effectively compose expressions to operate on
data frames.

The following was taken from https://dplyr.tidyverse.org/
- `mutate()` adds new variables that are functions of existing variables
- `select()` picks variables based on their names.
- `filter()` picks cases based on their values.
- `summarise()` reduces multiple values down to a single summary.
- `arrange()` changes the ordering of the rows.

```Rscript
library(dplyr, warn.conflicts = FALSE)

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
    # df.select(z=col('a') * 2),           # mutate(z = a * 2)
    # df.with_columns(z=col('a') * 2),           # mutate(z = a * 2)
    # df.select(cs.numeric() * 2),                   # select(where(is.numeric))
    # df.filter(col('a') >= 2),                  # filter(a >= 2)
    # df.select(col('a').mean()),                # summarise(mean(a), mean(b))
    df.group_by('group').agg(col('a').mean()), # group_by(group) %>% summarise(mean(a))
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

from pandas import read_csv as pd_read_csv # its been around for a long time; it has a lot of conveniences
from polars import col, from_pandas, Date, Int64, Int8

df = (
    pd_read_csv(buffer, sep=r'\s{2,}', engine='python')
    .pipe(from_pandas)
    .cast({'temperature': Int64})
    .with_columns(
        col('date').str.strptime(Date, format='%Y-%m-%d')
    )
)
# print(df)

# What is the weather on January 2nd?
from datetime import date
print(
    # df.filter(col('temperature') == 77)
    df.lazy().filter(col('date') == date(2020, 1, 2))
)

# How many days did it rain? How many days did it not rain?
# print(
#     df.select(col('precipitation').value_counts().struct.unnest())
# )

# What days were hotter than the preceding recorded day?
# print(
#     df.select(
#         (col('temperature') > col('temperature').shift()).value_counts()
#     )
# )

# What was the hottest day when it rained?
# print(
#     df.filter(col('precipitation'))
#     # .sort('temperature')
#     .top_k(3, by='temperature')
# )

# What were the longest and shortest streaks of rainy days in a row; when did they begin?
#from polars import len as pl_len
#print(
#     #df.with_columns(rle=col('precipitation').rle_id())
#     df.group_by(['precipitation', col('precipitation').rle_id().alias('id')])
#     .agg(
#        start=col('date').min(),
#        length=pl_len(),
#     )
#     .filter('precipitation')
#     .drop('precipitation')
#)
```

## Wrap Up

R and Python adopt distinct philosophies but converge on a similar underlying
concept for data structures: column-oriented, homogeneous vectors combined
into a heterogeneous table. R’s data.frame and Python’s polars.DataFrame
implement this model in ways that reflect their respective design priorities,
with R emphasizing concise syntax and non-standard evaluation, and Python
emphasizing explicit and composable expressions.

Polars provides a declarative framework for data transformation that
parallels R’s dplyr. Instead of performing in-place mutations, it builds
expressions that describe transformations and evaluate within a defined
context, whether over the entire DataFrame or within groups. This model
enables efficient execution and a clear separation between definition and
evaluation. Polars, can be evaluated in an entirely lazy fashion and has
a powerful query optimizer to help further speed up your queries similar
to dtplyr, dbplyr, etc.

Both ecosystems ultimately achieve a comparable balance between
expressiveness and precision, with Polars offering a structured and
performant interpretation of the DataFrame paradigm in Python.
