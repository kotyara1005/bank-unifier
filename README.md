# Bank unifier
## Requirements
Python3 standard library

## Help
```shell script
python banks_unifier.py -h
```

```
usage: banks_unifier.py [-h] [-o FILENAME] BANK_TYPE FILENAME [BANK_TYPE FILENAME ...]

Available bank types: BankA, BankB, BankC

positional arguments:
  BANK_TYPE FILENAME

optional arguments:
  -h, --help          show this help message and exit
  -o FILENAME
```
## Example
```shell script
python banks_unifier.py BankA data/bank1.csv BankB data/bank2.csv BankC data/bank3.csv
```

## Tests
```shell script
python -m unittest tests.py
```
