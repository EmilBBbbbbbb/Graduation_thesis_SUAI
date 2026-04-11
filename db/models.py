from sqlalchemy import Column, Table, MetaData, String, DateTime, Float, Integer, ForeignKey

metadata = MetaData()


users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(64), nullable=False, unique=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("password_hash", String(255), nullable=False),
    Column("start_capital", Float, nullable=False, default=100000.0),
    Column("current_capital", Float, nullable=False, default=100000.0),
    Column("created_at", DateTime, nullable=False),
)


demo_trades_table = Table(
    "demo_trades",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("metal_key", String(16), nullable=False, index=True),
    Column("side", String(8), nullable=False),
    Column("quantity", Float, nullable=False),
    Column("price", Float, nullable=False),
    Column("total", Float, nullable=False),
    Column("created_at", DateTime, nullable=False),
)

gold_cost_table = Table(
    'gold_cost',
    metadata,
Column('date', DateTime, primary_key=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),
    Column('volume', Integer),)

silver_cost_table = Table(
    'sliver_cost',
    metadata,
Column('date', DateTime, primary_key=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),
    Column('volume', Integer),)

copper_cost_table = Table(
    'copper_cost',
    metadata,
Column('date', DateTime, primary_key=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),
    Column('volume', Integer),)

gold_cost_predict_table = Table(
    'gold_predict_cost',
    metadata,
Column('date', DateTime, primary_key=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),)

silver_cost_predict_table = Table(
    'sliver_predict_cost',
    metadata,
Column('date', DateTime, primary_key=True),
    Column('open', Float),
    Column('high', Float),
    Column('low', Float),
    Column('close', Float),)

copper_cost_predict_table = Table(
    'copper_predict_cost',
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
