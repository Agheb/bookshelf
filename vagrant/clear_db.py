from bookshelf import db

meta = db.metadata
for table in reversed(meta.sorted_tables):
    print 'Clear table %s' % table
    db.session.execute(table.delete())
db.session.commit()
