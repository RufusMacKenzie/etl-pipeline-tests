import csv


def read_csv(filepath: str) -> list[dict]:
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)
