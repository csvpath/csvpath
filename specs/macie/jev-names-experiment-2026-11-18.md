# NAME and ADDRESS through Jev: the experiment, 2026-11-18

For `jev-names-addresses-design.md`. Can Jev tell, from a column's
masked shapes, its header and its neighbours, whether it holds people's
full names or postal addresses?

## What was asked

`tests/macie/live/jev_names_experiment.py`. There were 32 synthetic
columns of 200 rows each:

- 7 hold full names, including `Last, First`, middle initials, titles,
  all caps, hyphenated and `O'` names, and a vague `field_3` header;
- 7 hold addresses: US, UK, Canada (accents), Germany, France, an
  apartment, and a vague `field_4` header;
- 16 are look-alikes: product names, companies, cities, job titles,
  departments, street names, countries, usernames, emails, a street with
  no city or postcode, city and state with no postcode, ZIP codes alone,
  GPS, order references, dates and phones;
- 2 are ambiguous: first names alone (not a full name to Macie), and
  call notes with names inside sentences.

Each column was asked about both NAME and ADDRESS: 64 `choice()`
questions in 7 requests, to `jev-1.14.0`. The case-keeping mask was used
(`A` upper case, `a` lower case, `#` digit), so only shapes, headers and
counts were sent. Nothing was sent as written.

## Results

**57 of the 60 scored questions were right** taking the `choice` label
as given (`likely` means yes). The ambiguous 4 are not scored. There
were 16,683 tokens in and 2,823 out, about half a cent.

The three wrong were all close calls:

| Question | Truth | Answer | P(likely) |
|---|---|---|---|
| `street_only` (`#### Aaaa Aa`) as ADDRESS | no: no city or postcode | likely | 0.51 |
| `city_state` (`Aaaaaa, AA`) as ADDRESS | no: no postcode | likely | 0.50 |
| `vague_address` (`field_4`, US addresses) as NAME | no | likely | 0.61 |

Every true column scored at least 0.78 (`titled` 0.78, `uk_address`
0.80; most 0.88 to 0.98). **With a threshold of 0.7 on P(likely), all
60 are right.** The margin is narrow, though: 0.61 against 0.78.

The ambiguous columns:

| Question | Answer | P(likely) |
|---|---|---|
| `first_only` as NAME | doubtful | 0.15 |
| `notes_names` as NAME | doubtful | 0.18 |
| `notes_names` as ADDRESS | doubtful | 0.31 |

First names alone are not reported, which matches Macie's "full names
only". Names inside free text are missed, as the design expected: at
column level they cannot be found.

## What it says

- Column-level questions from masked shapes work for these columns: the
  header, the neighbours and the shapes are enough.
- **Use the probability, not the label**, with a threshold (0.7 from
  this run), as the review's design already does for its verdicts.
- The near misses are on Macie's own boundary: an address without a city
  or postcode. A postcode rule before the question (in the design) would
  remove those columns without asking Jev.
- These columns are synthetic and tidy. Real columns are messier, mixed
  and sparse, so road-testers should confirm.
