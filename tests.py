import io
import sys
import tempfile
from datetime import date
from unittest import TestCase
from unittest.mock import patch

from banks_unifier import (
    Bank,
    BankAReader,
    BankBReader,
    BankCReader,
    BankRecord,
    CsvWriter,
    OperationType,
    get_reader_for_bank,
    main,
    pipe,
)


class OutputRecordTest(TestCase):
    def test_get_fields(self):
        self.assertEqual(
            BankRecord.get_fields(), ["timestamp", "type", "amount", "from", "to"]
        )

    def test_as_dict(self):
        self.assertEqual(
            BankRecord(
                timestamp=date(2020, 2, 2),
                type=OperationType.REMOVE,
                amount=3.14,
                from_=1,
                to=2,
            ).as_dict(),
            {
                "amount": 3.14,
                "from": 1,
                "timestamp": date(2020, 2, 2),
                "to": 2,
                "type": "remove",
            },
        )


class GetRecordTest(TestCase):
    def test_get_record(self):
        output = BankRecord(
            timestamp=date(2019, 10, 1),
            type=OperationType.REMOVE,
            amount=3.04,
            from_=1,
            to=2,
        )
        test_cases = [
            (
                "bank a",
                {
                    "amount": "3.04",
                    "from": "1",
                    "timestamp": "Oct 1 2019",
                    "to": "2",
                    "type": "remove",
                },
                BankAReader(io.StringIO()).transform,
            ),
            (
                "bank b",
                {
                    "amounts": "3.04",
                    "from": "1",
                    "date": "01-10-2019",
                    "to": "2",
                    "transaction": "remove",
                },
                BankBReader(io.StringIO()).transform,
            ),
            (
                "bank c",
                {
                    "euro": "3",
                    "cents": "4",
                    "from": "1",
                    "date_readable": "1 Oct 2019",
                    "to": "2",
                    "type": "remove",
                },
                BankCReader(io.StringIO()).transform,
            ),
        ]
        for name, data, func in test_cases:
            with self.subTest(name):
                self.assertEqual(
                    func(data), output,
                )

    def test_get_reader_func(self):
        test_cases = [
            (Bank.BANK_A, BankAReader),
            (Bank.BANK_B, BankBReader),
            (Bank.BANK_C, BankCReader),
        ]
        for bank_type, func in test_cases:
            with self.subTest():
                self.assertEqual(get_reader_for_bank(bank_type), func)


class CsvWriterTest(TestCase):
    def test(self):
        buf = io.StringIO()
        record = BankRecord(
            timestamp=date(2019, 10, 1),
            type=OperationType.REMOVE,
            amount=3.04,
            from_=1,
            to=2,
        )
        CsvWriter(buf).write(record)

        self.assertEqual(
            buf.getvalue(),
            "timestamp,type,amount,from,to\r\n2019-10-01,remove,3.04,1,2\r\n",
        )


class ParserTest(TestCase):
    def test(self):
        test_data = "\r\n".join(
            [
                "timestamp,type,amount,from,to",
                "Oct 1 2019,remove,99.20,198,182",
                "Oct 2 2019,add,2000.10,188,198",
            ]
        )

        buf = io.StringIO()
        pipe(
            reader=BankAReader(io.StringIO(test_data)), writer=CsvWriter(buf),
        )
        self.assertEqual(
            buf.getvalue(),
            "timestamp,type,amount,from,to\r\n2019-10-01,remove,99.2,198,182\r\n2019-10-02,add,2000.1,188,198\r\n",
        )


class MainTest(TestCase):
    def test(self):

        with tempfile.NamedTemporaryFile() as file:
            testargs = [
                "",  # executable should be first
                "BankA",
                "data/bank1.csv",
                "BankB",
                "data/bank2.csv",
                "BankC",
                "data/bank3.csv",
                "-o",
                file.name,
            ]
            with patch.object(sys, "argv", testargs):
                result = main()
                self.assertEqual(result, None)
                self.assertEqual(
                    file.read().decode(),
                    "\r\n".join(
                        [
                            "timestamp,type,amount,from,to",
                            "2019-10-01,remove,99.2,198,182",
                            "2019-10-02,add,2000.1,188,198",
                            "2019-10-03,remove,99.4,198,182",
                            "2019-10-04,add,2123.5,188,198",
                            "2019-10-05,remove,5.07,198,182",
                            "2019-10-06,add,1060.08,188,198",
                            "",
                        ]
                    ),
                )
