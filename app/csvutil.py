# -*- coding: utf-8 -*-

import csv
import codecs
import cStringIO


def from_str(value):
    if value == '':
        value = None
    return value


def to_str(value):
    if value is None:
        value = ''
    return value


class UTF8Recoder:
    '''
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    '''
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def next(self):
        return self.reader.next().encode('utf-8')

    def __iter__(self):
        return self


class UnicodeReader:
    '''
    A CSV reader which will iterate over lines in the CSV file 'f',
    which is encoded in the given encoding.
    '''

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [from_str(unicode(s, 'utf-8')) for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    '''
    A CSV writer which will write rows to CSV file 'f',
    which is encoded in the given encoding.
    '''

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([to_str(s).encode('utf-8') for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)