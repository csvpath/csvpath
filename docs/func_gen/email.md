
Email

A line() schema type indicating that the value it represents must be an email

| Data signatures               |
|:------------------------------|
| email( address: str|None|'' ) |

| Call signatures                                      |
|:-----------------------------------------------------|
| email( address: Header|Variable|Reference|Function ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | email() determines if lines match |
| Type       | Email is a line() schema type     |

| Context          | Qualifier                  |
|:-----------------|:---------------------------|
| Match qualifiers | onmatch, notnone, distinct |
| Value qualifiers | onmatch, notnone           |


