from sqlalchemy import Column, Table, MetaData, String, DateTime, Float, Integer

metadata = MetaData()

gold_cost_table = Table(
    'gold_cost',
    metadata,
Column('date', DateTime, primary_key=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),)

silver_cost_table = Table(
    'sliver_cost',
    metadata,
Column('date', DateTime, primary_key=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),)

copper_cost_table = Table(
    'copper_cost',
    metadata,
Column('date', DateTime, primary_key=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),)

gold_news_table = Table(
    'gold_news',
    metadata,
Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String),
    Column('description', String),
    Column('full_text', String),
    Column('date', DateTime),
    Column('url', String),)

silver_news_table = Table(
    'sliver_news',
    metadata,
Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String),
    Column('description', String),
    Column('full_text', String),
    Column('date', DateTime),
    Column('url', String),)

copper_news_table = Table(
    'copper_news',
    metadata,
Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String),
    Column('description', String),
    Column('full_text', String),
    Column('date', DateTime),
    Column('url', String),)
