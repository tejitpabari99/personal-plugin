#!/usr/bin/env python3
"""Synthetic regression checks; no private source data or network writes."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
import granola as g


def meeting(number, date, title='A 😀 title'):
    row = {key: '' for key in g.FIELDS}
    row.update(document_id=f'00000000-0000-4000-8000-{number:012d}', document_title=title, document_created=date+'T12:00:00Z', summary='# Heading\n\n- A, B\n  - C\n', transcript='hello, there\n"quoted" 😀\r\nend')
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'export.csv'
        with path.open('w', newline='') as out:
            writer=csv.DictWriter(out,fieldnames=g.FIELDS); writer.writeheader(); writer.writerow(row)
        return g.read_export(path)[0]


def simulate(batch, text='\n', normalized=False):
    ranges={}
    for req in batch['requests']:
        if 'insertText' in req:
            r=req['insertText']; index=r['location']['index']-1
            # Python indexes must be translated from UTF-16 for emoji fixtures.
            prefix=text.encode('utf-16-le')[:index*2].decode('utf-16-le')
            suffix=text.encode('utf-16-le')[index*2:].decode('utf-16-le')
            text=prefix+r['text']+suffix
        if 'createNamedRange' in req:
            r=req['createNamedRange']; ranges[r['name']]={'namedRanges':[dict(name=r['name'],namedRangeId=r['name'],ranges=[r['range']])]}
    tab={'body':{'content':[{'endIndex':g.utf16(text)+1}]},'namedRanges':ranges}
    if normalized:
        doc={'tabs':[dict(tab,tabId='t.0')]}
    else:
        doc={'tabs':[{'tabProperties':{'tabId':'t.0'},'documentTab':tab}]}
    return text,doc


class Tests(unittest.TestCase):
    def test_csv_roundtrip(self):
        m=meeting(1,'2026-10-01')
        self.assertEqual(m['source_record']['transcript'],'hello, there\n"quoted" 😀\r\nend')
        self.assertEqual(g.utf16('😀'),2)

    def test_order_and_rerun(self):
        items=[meeting(i,f'2026-10-{i:02d}') for i in range(1,6)]
        for normalized in [False,True]:
            initial=g.build_batch([items[1],items[3]],{},[],tab_id='t.0')
            text,doc=simulate(initial,normalized=normalized)
            batch=g.build_batch([items[0],items[2],items[4]],doc,[items[1],items[3]],tab_id='t.0')
            text,doc=simulate(batch,text,normalized)
            expected=''.join(g.section(m)[0] for m in reversed(items))+'\n'
            self.assertEqual(text,expected)
            for mid,index in g.named_positions(doc).items():
                tail=text.encode('utf-16-le')[(index-1)*2:].decode('utf-16-le')
                self.assertRegex(tail,r'^2026-10-\d{2} - ',mid)
            self.assertEqual(g.build_batch(items,doc,items,tab_id='t.0')['requests'],[])

    def test_multitab_isolation(self):
        old,new,unrelated=meeting(1,'2026-10-01'),meeting(2,'2026-10-02'),meeting(3,'2026-10-03')
        text,doc=simulate(g.build_batch([old],{},[],tab_id='t.0'),normalized=True)
        _,other=simulate(g.build_batch([unrelated],{},[],tab_id='t.other'),normalized=True)
        other['tabs'][0]['tabId']='t.other'
        doc['tabs'].extend(other['tabs'])
        batch=g.build_batch([new],doc,[old],tab_id='t.0')
        self.assertEqual(set(batch['ordered_meeting_ids']),{old['meeting_id'],new['meeting_id']})
        for req in batch['requests']:
            if 'deleteNamedRange' in req:
                self.assertEqual(req['deleteNamedRange']['tabsCriteria'],{'tabIds':['t.0']})
                self.assertNotIn('tabId',req['deleteNamedRange'])
        with self.assertRaises(ValueError):g.build_batch([new],doc,[old])

    def test_archive_personal_tags_and_index(self):
        m=meeting(8,'2026-10-08','[Personal] CDR planning')
        self.assertTrue(g.is_personal(m))
        self.assertTrue(g.is_personal(meeting(9,'2026-10-09','Other [personal] idea')))
        self.assertFalse(g.is_personal(meeting(10,'2026-10-10','Personalized tools')))
        raw=g.transcript_payload(m)
        self.assertEqual(set(raw),{'meeting_id','transcript'})
        meta=g.metadata_payload(m,['CDR','personal','cdr'],'Explore audit dimensions.')
        self.assertNotIn('transcript',meta)
        self.assertEqual(meta['tags'],['cdr','personal'])
        self.assertEqual(meta['kind'],'personal')
        heading=g.section(m)[0].splitlines()[0]
        self.assertEqual(heading,'2026-10-08 - [Personal] CDR planning')
        group=dict(organization='Personal',organization_brief='Private notes.',folder_url='folder-url',notes_document_url='doc-url',meetings={m['meeting_id']:meta})
        text=g.render_index('General Meetings',[group])
        self.assertIn('Latest: 2026-10-08',text)
        self.assertIn('Explore audit dimensions.',text)
        self.assertEqual(text.count('  2026-10-08 -'),1)

    def test_bad_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv';p.write_text(','.join(g.FIELDS)+'\na,b\n')
            with self.assertRaises(ValueError):g.read_export(p)
            p.write_text(','.join(g.FIELDS)+'\n"unterminated')
            with self.assertRaises(csv.Error):g.read_export(p)

    def test_duplicate_conflict(self):
        row=meeting(1,'2026-10-01')['source_record']
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'duplicate.csv'
            with p.open('w',newline='') as out:
                w=csv.DictWriter(out,fieldnames=g.FIELDS);w.writeheader();w.writerow(row);w.writerow(row)
            self.assertEqual(len(g.read_export(p)),1)
            with p.open('a',newline='') as out:
                csv.DictWriter(out,fieldnames=g.FIELDS).writerow(dict(row,transcript='different'))
            with self.assertRaises(ValueError):g.read_export(p)


if __name__=='__main__':unittest.main()
