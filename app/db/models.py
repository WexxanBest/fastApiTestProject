from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey, Enum as SaEnum
from sqlalchemy.ext.declarative import declarative_base


# SQLAlchemy рекомендует использовать единый формат для генерации названий для
# индексов и внешних ключей.
# https://docs.sqlalchemy.org/en/13/core/constraints.html#configuring-constraint-naming-conventions
convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class Type(str, Enum):
    CATEGORY = 'CATEGORY'
    OFFER = 'OFFER'


class ShopUnitsDB(Base):
    __tablename__ = 'shop_units'
    id = Column('id', String, primary_key=True, nullable=False)
    name = Column('name', String, nullable=False)
    date = Column('date', DateTime, nullable=False)
    parentId = Column('parentId', String, ForeignKey('shop_units.id', ondelete='CASCADE'), nullable=True)
    type = Column('type', SaEnum(Type, name='type'), nullable=False)
    price = Column('price', Integer, nullable=True)


class StatisticsDB(Base):
    __tablename__ = 'statistics'

    id = Column('id', String, ForeignKey('shop_units.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    name = Column('name', String, nullable=False)
    date = Column('date', DateTime, nullable=False, primary_key=True)
    parentId = Column('parentId', String, ForeignKey('shop_units.id'), nullable=True)
    type = Column('type', SaEnum(Type, name='type'), nullable=False)
    price = Column('price', Integer, nullable=True)


