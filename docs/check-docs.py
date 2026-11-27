#!/usr/bin/env python3
# docs/check-docs.py -- the documentation check (AGENTS.md, "Documentation"). Stdlib only.
#
#   python3 docs/check-docs.py          (from the repository root)
#
# A set is a top-level folder <set>/ holding a bundle <set>/<set>/ with at least one *.node.json. For each set it
# checks the layout of its docs, the descriptors' description and help text, that the user docs name every node,
# and that the bundle's docs don't link out of the bundle. It also checks that the root README indexes every set.
#
# Exit 0 when every check passes. A KNOWN GAP is a problem we know about: it's reported without failing the run, and
# fails the run once it no longer matches anything, so the entry gets removed.

import glob
import json
import os
import re
import sys

# (regex matched against a problem line, why it's open)
KNOWN_GAPS = [
    (r"^home-assistant: no docs/how-it-works\.md$", 'not written yet'),
    (r"^home-assistant/home-assistant/ha_\w+\.node\.json: property '\w+' has no help$",
     'help text to be added to the HA descriptors'),
]

LINK = re.compile(r'\]\(([^)\s]+)\)')


def sets():
    for d in sorted(os.listdir('.')):
        if not d.startswith('.') and glob.glob(os.path.join(d, d, '*.node.json')):
            yield d


def bundle_docs(s):
    bundle = os.path.join(s, s)
    return [p for p in [os.path.join(bundle, 'README.md')] + sorted(glob.glob(os.path.join(bundle, 'docs', '*.md')))
            if os.path.exists(p)]


def check_set(s, problems):
    bundle = os.path.join(s, s)
    for path, what in ((os.path.join(s, 'README.md'), 'README.md'),
                       (os.path.join(bundle, 'README.md'), '%s/README.md' % s),
                       (os.path.join(s, 'docs', 'how-it-works.md'), 'docs/how-it-works.md'),
                       (os.path.join(s, 'THINGSTUDIO_VERSION'), 'THINGSTUDIO_VERSION')):
        if not os.path.exists(path):
            problems.append('%s: no %s' % (s, what))
    if os.path.exists(os.path.join(s, 'docs', 'working-notes', 'SPEC.md')):
        problems.append('%s: SPEC.md belongs in docs/, not docs/working-notes/' % s)

    docs = bundle_docs(s)
    text = ''.join(open(p, encoding='utf-8').read() for p in docs)
    for path in sorted(glob.glob(os.path.join(bundle, '*.node.json'))):
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        if not d.get('description'):
            problems.append('%s: no description' % path)
        for prop in d.get('properties', []):
            if prop.get('kind') != 'configRef' and not prop.get('help'):
                problems.append("%s: property '%s' has no help" % (path, prop.get('name')))
        label = d.get('label') or d.get('type')
        if label not in text:
            problems.append("%s: node '%s' isn't named in the bundle's docs" % (path, label))

    top = os.path.abspath(bundle)
    for path in docs:
        for target in LINK.findall(open(path, encoding='utf-8').read()):
            if re.match(r'^(https?:|mailto:|#)', target):
                continue
            dest = os.path.abspath(os.path.join(os.path.dirname(path), target.split('#')[0]))
            if not (dest == top or dest.startswith(top + os.sep)):
                problems.append('%s: link %s leaves the bundle (it breaks once the bundle is installed)' % (path, target))
            elif not os.path.exists(dest):
                problems.append('%s: link %s points at nothing' % (path, target))


def main():
    problems = []
    found = list(sets())
    readme = open('README.md', encoding='utf-8').read() if os.path.exists('README.md') else ''
    for s in found:
        if '](%s/)' % s not in readme:
            problems.append("README.md: set '%s' isn't in the index" % s)
        check_set(s, problems)

    failed, gaps, used = [], [], set()
    for p in problems:
        hit = next((i for i, (rx, _) in enumerate(KNOWN_GAPS) if re.search(rx, p)), None)
        if hit is None:
            failed.append(p)
        else:
            used.add(hit)
            gaps.append('KNOWN GAP (%s): %s' % (KNOWN_GAPS[hit][1], p))
    for i, (rx, why) in enumerate(KNOWN_GAPS):
        if i not in used:
            failed.append('KNOWN GAP fixed, remove it from KNOWN_GAPS: %s (%s)' % (rx, why))

    for g in gaps:
        print(g)
    for f in failed:
        print('FAIL ' + f)
    print('docs: %d sets (%s), %d failures, %d known gaps' % (len(found), ', '.join(found), len(failed), len(gaps)))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
