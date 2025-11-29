# Lookups


We want a simple order doc that has a SIC code.


When we process the orders we look up the sic-code using: `in(#code,
$sic#lookup.headers.SIC)`


To work we need the SIC lookup data to be available ahead of the run.

