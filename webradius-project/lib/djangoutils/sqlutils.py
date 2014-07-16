# -*- coding: utf-8 -*-

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

def runsql(sql,**kwargs):
	database = kwargs.get('database') or 'default'
	operation = kwargs.get('operation') or 'select'

    from django.db import connection, transaction
   	cursor = connections[database].cursor()

	if operation == 'select':
    	# Data retrieval operation - no commit required
    	cursor.execute(sql)
    	return dictfetchall(cursor)
    else:
    	# Data modifying operation - commit required
    	cursor.execute(sql)
    	transaction.commit_unless_managed(using=database)
    	return None