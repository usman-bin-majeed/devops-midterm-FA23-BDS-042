"""Compare the previous deployed model with the new one and write report.html.

Usage: python3 scripts/report.py prev_metrics.json metrics.json report.html
Standard library only: it runs on the Jenkins host.
"""
import html
import json
import sys
from pathlib import Path


def load(path):
    try:
        data = json.loads(Path(path).read_text() or '{}')
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def main():
    prev, new, out = load(sys.argv[1]), load(sys.argv[2]), Path(sys.argv[3])
    old_acc, new_acc = prev.get('accuracy'), new.get('accuracy')

    if old_acc is None:
        verdict = 'First deployment (no previous model to compare).'
    elif new_acc > old_acc:
        verdict = f'Accuracy INCREASED by {new_acc - old_acc:+.4f}.'
    elif new_acc < old_acc:
        verdict = f'Accuracy DECREASED by {new_acc - old_acc:+.4f}.'
    else:
        verdict = 'Accuracy UNCHANGED.'

    fields = ['accuracy', 'training_rows', 'model_version', 'git_sha']
    rows = ''.join(
        f'<tr><td>{f}</td><td>{html.escape(str(prev.get(f, "-")))}</td>'
        f'<td><b>{html.escape(str(new.get(f, "-")))}</b></td></tr>'
        for f in fields
    )
    out.write_text(
        f'<p><b>{html.escape(verdict)}</b></p>'
        '<table border="1" cellpadding="6" cellspacing="0">'
        '<tr><th>Metric</th><th>Previous model</th><th>New model</th></tr>'
        f'{rows}</table>'
    )
    print(verdict)


if __name__ == '__main__':
    main()
