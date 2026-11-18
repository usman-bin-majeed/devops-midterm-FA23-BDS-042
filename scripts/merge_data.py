"""Fold any extra CSV files pushed into dataset/ into dataset/train.csv.

New data may arrive either as rows appended to dataset/train.csv (nothing to do)
or as separate CSV files (e.g. dataset/new_batch.csv). This script appends the
rows of every extra CSV that has the required columns, so train.py always sees
all available data. Standard library only: it runs on the Jenkins host.
"""
import csv
import json
from pathlib import Path

DATASET_DIR = Path('dataset')
TRAIN = DATASET_DIR / 'train.csv'


def main():
    config = json.loads(Path('config.json').read_text())
    required = config['features'] + ['label']

    with TRAIN.open(newline='') as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames
        rows = list(reader)
    base_rows = len(rows)

    extras = sorted(p for p in DATASET_DIR.rglob('*.csv') if p.resolve() != TRAIN.resolve())
    for path in extras:
        with path.open(newline='') as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames or not set(required).issubset(reader.fieldnames):
                print(f'skip {path}: missing required columns')
                continue
            new = [{col: r.get(col, '') for col in header} for r in reader]
        rows.extend(new)
        print(f'merged {len(new)} rows from {path}')

    if len(rows) != base_rows:
        with TRAIN.open('w', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=header, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    print(f'training rows: {len(rows)} (train.csv had {base_rows})')


if __name__ == '__main__':
    main()
