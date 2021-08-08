import argparse
import csv
import pathlib
import sys
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime
from enum import Enum, unique
from typing import Iterator, List, Optional, TextIO, Tuple, Type


class ValidationError(Exception):
    pass


class StrEnum(str, Enum):
    """
        Recipe from standard library
        https://docs.python.org/3/library/enum.html#others
    """

    pass


@unique
class Bank(StrEnum):
    BANK_A = "BankA"
    BANK_B = "BankB"
    BANK_C = "BankC"


@unique
class OperationType(StrEnum):
    REMOVE = "remove"
    ADD = "add"


@dataclass
class BankRecord:
    """Unified bank record"""

    timestamp: date
    type: OperationType
    amount: float
    from_: int
    to: int

    @classmethod
    def get_fields(cls):
        """Fields for unified file"""
        replace = {"from_": "from"}
        return [replace.get(field.name, field.name) for field in fields(cls)]

    def as_dict(self):
        result = asdict(self)
        result["from"] = result.pop("from_")
        return result


class AbstractReader:
    """This class reads data from file and transforms to BankRecord"""

    def __init__(self, file: TextIO):
        self.file = file

    def __iter__(self) -> Iterator[BankRecord]:
        for record in csv.DictReader(self.file):
            yield self.transform(record)

    def transform(self, record: dict) -> BankRecord:
        raise NotImplementedError()


class BankAReader(AbstractReader):
    def transform(self, record: dict) -> BankRecord:
        """Validate and transform BankA record to general bank record"""
        try:
            return BankRecord(
                timestamp=datetime.strptime(record["timestamp"], "%b %d %Y").date(),
                type=OperationType(record["type"]),
                amount=float(record["amount"]),
                from_=int(record["from"]),
                to=int(record["to"]),
            )
        except (KeyError, ValueError) as error:
            raise ValidationError(f"invalid data for bank a: {error}")


class BankBReader(AbstractReader):
    def transform(self, record: dict) -> BankRecord:
        """Validate and transform Bank B record to general bank record"""
        try:
            return BankRecord(
                timestamp=datetime.strptime(record["date"], "%d-%m-%Y").date(),
                type=OperationType(record["transaction"]),
                amount=float(record["amounts"]),
                from_=int(record["from"]),
                to=int(record["to"]),
            )
        except (KeyError, ValueError) as error:
            raise ValidationError(f"invalid data for bank b: {error}")


class BankCReader(AbstractReader):
    def transform(self, record: dict) -> BankRecord:
        """Validate and transform Bank C record to general bank record"""
        try:
            return BankRecord(
                timestamp=datetime.strptime(record["date_readable"], "%d %b %Y").date(),
                type=OperationType(record["type"]),
                amount=int(record["euro"]) + int(record["cents"]) / 100,
                from_=int(record["from"]),
                to=int(record["to"]),
            )
        except (KeyError, ValueError) as error:
            raise ValidationError(f"invalid data for bank c: {error}")


def get_reader_for_bank(bank: Bank) -> Type[AbstractReader]:
    """Choose transform function by bank name"""
    return {
        Bank.BANK_A: BankAReader,
        Bank.BANK_B: BankBReader,
        Bank.BANK_C: BankCReader,
    }[bank]


class AbstractWriter:
    def write(self, record: BankRecord):
        raise NotImplementedError()


class CsvWriter(AbstractWriter):
    def __init__(self, file: TextIO):
        self.writer = csv.DictWriter(file, fieldnames=BankRecord.get_fields())
        self.writer.writeheader()

    def write(self, record: BankRecord):
        self.writer.writerow(record.as_dict())


def pipe(reader: AbstractReader, writer: AbstractWriter):
    """Send records from reader to writer"""
    for row in reader:
        writer.write(row)


def parse_args() -> Tuple[List[Tuple[pathlib.Path, Bank]], str]:
    parser = argparse.ArgumentParser(description=f"Available bank types: {', '.join(Bank)}")
    parser.add_argument("files", nargs="+", metavar="BANK_TYPE FILENAME")
    parser.add_argument("-o", type=str, metavar="FILENAME", default="output.csv")
    args = parser.parse_args()

    if len(args.files) % 2:
        parser.error("files arg should be pairs of values")

    files = []
    for bank_name, filename in zip(args.files[::2], args.files[1::2]):
        path = pathlib.Path(filename)
        if not path.exists():
            parser.error(f"path {path} does not exist")

        if not path.is_file():
            parser.error(f"path {path} is not a file")

        try:
            bank_name = Bank(bank_name)
        except ValueError:
            parser.error(f"unknown bank type: {bank_name}")

        files.append((path, bank_name))

    return files, args.o


def main() -> Optional[int]:
    file_pairs, filename = parse_args()

    with open(filename, "w") as output:
        writer = CsvWriter(output)
        for path, bank_type in file_pairs:
            with path.open() as file:
                try:
                    pipe(get_reader_for_bank(bank_type)(file), writer)
                except ValidationError as error:
                    print(str(error), file=sys.stderr)
                    return 1


if __name__ == "__main__":
    sys.exit(main())
