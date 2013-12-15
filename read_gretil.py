#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Reads from a GRETIL UTF-8 encoded HTML file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import json
import logging
import os.path
import re
import sys

import handle_input
import sscan


def ToUnicode(x):
  if isinstance(x, unicode):
    return x
  if isinstance(x, int):
    return unicode(x)
  if isinstance(x, list):
    return ListToUnicode(x)
  if isinstance(x, dict):
    return DictToUnicode(x)
  assert False, (x, type(x))


def ListToUnicode(li):
  assert isinstance(li, list)
  ret = ('[' + ', '.join(ToUnicode(i) for i in li) + ']')
  assert isinstance(ret, unicode)
  return ret


def DictToUnicode(d):
  assert isinstance(d, dict)
  ret = '{'.encode('utf-8')
  for (key, value) in sorted(d.items(), key=lambda x: x[1], reverse=True):
    ret += ('\n  ' + key + ': ' + ToUnicode(value)).encode('utf-8')
  ret += '\n}'.encode('utf-8')
  assert isinstance(ret, str)
  ret = ret.decode('utf-8')
  assert isinstance(ret, unicode)
  return ret


def Print(u):
  u = ToUnicode(u)
  assert isinstance(u, unicode), (u, type(u))
  print(u.encode('utf8'))

if __name__ == '__main__':
  assert len(sys.argv) == 2
  input_file_name = sys.argv[1]

  logger = logging.getLogger()
  handler = logging.FileHandler('/var/tmp/read_gretil.log')
  handler.setFormatter(logging.Formatter(
      '%(levelname)s	%(asctime)s %(filename)s:%(lineno)d] %(message)s'))
  logger.addHandler(handler)
  logger.setLevel(logging.DEBUG)

  lines = []
  seen_separators = 0
  for l in open(input_file_name, 'r'):
    l = l.decode('utf8')
    l = handle_input.RemoveHTML(l)
    l = l.strip()
    if seen_separators < 2 and re.search('<![-]{50,}->', l):
      seen_separators += 1
    elif seen_separators == 2 and not l.startswith('<'):
      (l, n) = handle_input.RemoveVerseNumber(l)
      lines.append(l)
      if n:
        lines.append('')

  verses = handle_input.BreakIntoVerses(lines)
  known_non_verses = [['{ūttarameghaḥ}'], ['iti śubhaṃ bhūyāt |']]
  verses = [verse for verse in verses if verse not in known_non_verses]

  identifier = sscan.Identifier()
  table = {}
  for (verse_number, verse) in enumerate(verses):
    verse = [l.strip() for l in verse]
    metre = identifier.IdentifyFromLines(verse)
    if not metre:
      clean = identifier.cleaned_output[1:]
      if not ''.join(clean):
        continue
      table['unknown'] = table.get('unknown', 0) + 1
      Print('Verse %4d:' % (verse_number + 1))
      Print('\n'.join(verse))
      Print(identifier.AllDebugOutput())
      Print('')
      continue
    assert metre
    assert isinstance(metre, list)
    metre_name = None
    if len(metre) == 1 and not metre[0].issues:
      metre_name = metre[0].MetreName()
      Print('Verse %4d is in %s' % (verse_number + 1, metre_name))
    else:
      all_metres = set(m.MetreNameOnlyBase() for m in metre)
      assert len(all_metres) == 1, (all_metres, verse)
      metre_name = all_metres.pop()
      Print('Verse %4d is in %s (probably), but it has issues'
            % (verse_number + 1, metre_name))
    table[metre_name] = table.get(metre_name, 0) + 1

  sum_counts = sum(value for (key, value) in table.items())
  for (metre, count) in table.items():
    table[metre] = [count, '%.2f%%' % (count * 100 / sum_counts)]
  Print(table)

  stats_file_name = os.path.basename(input_file_name) + '.stats'
  stats_file = codecs.open(stats_file_name, 'w', 'utf-8')
  json.dump(table, stats_file, indent=2, ensure_ascii=False)
  stats_file.close()
  stats_file = codecs.open(stats_file_name, 'r', 'utf-8')
  assert table == json.load(stats_file, 'utf-8')
