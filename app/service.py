from datetime import datetime, timedelta
from typing import Union, Tuple, List, Dict

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.exceptions import HTTPException

from app.db.models import ShopUnitsDB, StatisticsDB
from app.schemas import (ShopUnit, ShopUnitImportRequest, ShopUnitImport, ShopUnitType,
                         ShopUnitStatisticsResponse)


async def import_shop_units(db: AsyncSession, import_rq: ShopUnitImportRequest):
    update_dt = import_rq.updateDate
    items = import_rq.items

    validated = await validate_items(db, items, update_dt)
    to_add = validated.pop('__add__')
    to_update = validated.pop('__update__')

    for item_id, item in validated.items():
        if item_id in to_add:
            await add_new_shop_unit(db, item)
        else:
            await update_shop_unit(db, item)

    await db.commit()
    print(items)


async def recount_prices(db: AsyncSession, shop_units: List[ShopUnit]):
    ids = [shop_unit.id for shop_unit in shop_units]
    roots = await find_roots(db, ids)
    print(roots)
    for root in roots:
        await assign_shop_unit_children(db, root, update_price_in_DB=True)

    await db.commit()


async def find_roots(db: AsyncSession, shop_unit_ids: List[str], roots=None):
    if roots is None:
        roots = []

    for shop_unit_id in shop_unit_ids:
        shop_unit = await get_shop_unit(db, shop_unit_id)
        shop_unit_parent_id = shop_unit[0].parentId
        if shop_unit[0].parentId is None:
            roots.append(shop_unit_id)
        else:
            await find_roots(db, [shop_unit_parent_id], roots)

    return roots


async def validate_items(db: AsyncSession, items: List[ShopUnitImport], dt: datetime) \
        -> Union[Dict[str, ShopUnit], None]:
    items_dict = {item.id: item for item in items}
    validated = dict(__add__=[], __update__=[])

    for item in items:
        if item.id in validated:
            continue
        await validate_item(db, item, items_dict, validated, dt)

    return validated


async def validate_item(db: AsyncSession, item: ShopUnitImport, import_items_dict: Dict[str, ShopUnitImport],
                        validated: Dict[str, ShopUnit], dt: datetime):
    res = await get_shop_unit(db, item.id)
    if res:
        action = 'update'
        obj, db_obj = res
    else:
        action = 'add'

    if item.parentId:
        if parent := await get_shop_unit(db, item.parentId):
            if parent[0].type == ShopUnitType.OFFER:
                raise HTTPException(400, "Wrong 'ShopUnitType' of parent!")

        elif item.parentId in validated:
            if validated[item.parentId].type == ShopUnitType.OFFER:
                raise HTTPException(400, "Wrong 'ShopUnitType' of parent!")

        elif item.parentId in import_items_dict:
            await validate_item(db, import_items_dict[item.parentId], import_items_dict, validated, dt)
            if validated[item.parentId].type == ShopUnitType.OFFER:
                raise HTTPException(400, "Wrong 'ShopUnitType' of parent!")
        else:
            raise HTTPException(400, f"No such parent with ID: {item.parentId}")

    if action == 'add':
        validated["__add__"].append(item.id)

    if action == 'update':
        if obj.type != item.type:
            raise HTTPException(400, "Type was changed!")
        validated["__update__"].append(item.id)

    validated[item.id] = ShopUnit(**item.dict(), date=dt)


async def get_shop_unit(db: AsyncSession, unit_id: str, children=False) -> Union[Tuple[ShopUnit, ShopUnitsDB], None]:
    db_obj = await db.execute(select(ShopUnitsDB).where(ShopUnitsDB.id == unit_id))
    db_obj = db_obj.scalar()
    if db_obj:
        obj = ShopUnit.from_orm(db_obj)
    else:
        return None

    if children:
        await assign_shop_unit_children(db, obj)

    return obj, db_obj


async def assign_shop_unit_children(db: AsyncSession, shop_unit: Union[ShopUnit, str], recursive: bool = True,
                                    update_price_in_DB=False):
    if isinstance(shop_unit, str):
        shop_unit = await get_shop_unit(db, shop_unit)
        shop_unit = shop_unit[0]
    children = await db.execute(select(ShopUnitsDB).where(ShopUnitsDB.parentId == shop_unit.id))
    children = children.scalars().all()
    children = db_objects_to_schema(children, ShopUnit)

    if children:
        shop_unit.children = children
    else:
        shop_unit.children = None

    children_price = 0
    if recursive:
        for child in children:
            await assign_shop_unit_children(db, child)
            if child.price:
                children_price += child.price

    if children_price and shop_unit.type == ShopUnitType.CATEGORY:
        shop_unit.price = children_price
        if update_price_in_DB:
            db_obj = await get_shop_unit(db, shop_unit.id)
            db_obj[1].price = children_price


async def update_shop_unit(db: AsyncSession, shop_unit: Union[ShopUnitImport, ShopUnit], dt: datetime = None):
    if isinstance(shop_unit, ShopUnitImport):
        shop_unit = ShopUnit(**shop_unit.dict(), date=dt)
    add_shop_unit_to_statistics_DB(db, shop_unit)

    obj, db_obj = await get_shop_unit(db, shop_unit.id)

    db_obj.id = shop_unit.id
    db_obj.type = shop_unit.type
    db_obj.parentId = shop_unit.parentId
    db_obj.name = shop_unit.name
    db_obj.price = shop_unit.price
    db_obj.date = shop_unit.date


async def add_new_shop_unit(db: AsyncSession, shop_unit: Union[ShopUnitImport, ShopUnit], dt: datetime = None):
    if isinstance(shop_unit, ShopUnitImport):
        shop_unit = ShopUnit(**shop_unit.dict(), date=dt)

    add_shop_unit_to_statistics_DB(db, shop_unit)

    shop_unit_dict: dict = shop_unit.dict()
    if 'children' in shop_unit_dict:
        shop_unit_dict.pop('children')
    db_obj = ShopUnitsDB(**shop_unit_dict)
    db.add(db_obj)


async def delete_shop_unit(db: AsyncSession, unit_id: str, commit=True):
    obj = await get_shop_unit(db, unit_id)
    if not obj:
        return False

    obj, db_obj = obj
    await db.delete(db_obj)

    if commit:
        await db.commit()
    return True


def add_shop_unit_to_statistics_DB(db: AsyncSession, shop_unit: ShopUnit):
    shop_unit_dict: dict = shop_unit.dict()
    if 'children' in shop_unit_dict:
        shop_unit_dict.pop('children')
    print(shop_unit_dict)
    stat_obj = StatisticsDB(**shop_unit_dict)
    db.add(stat_obj)


async def get_all_shop_units(db: AsyncSession):
    objects = await db.execute(select(ShopUnitsDB).order_by(ShopUnitsDB.id))
    objects = objects.scalars().all()
    res = []
    for obj in objects:
        res.append(ShopUnit.from_orm(obj))
    return res, objects


async def get_unit_statistics(db: AsyncSession, unit_id: str, date_start: datetime, date_end: datetime) \
        -> ShopUnitStatisticsResponse:
    rows = await db.execute(select(StatisticsDB).where(
        and_(StatisticsDB.id == unit_id,
             StatisticsDB.date >= date_start,
             StatisticsDB.date <= date_end)))
    rows = rows.scalars().all()
    rows = db_objects_to_schema(rows, ShopUnit)
    res = ShopUnitStatisticsResponse(items=rows)
    return res


async def get_sales(db: AsyncSession, dt: datetime):
    rows = await db.execute(select(ShopUnitsDB).where(and_(
        ShopUnitsDB.date >= dt - timedelta(hours=24),
        ShopUnitsDB.type == ShopUnitType.OFFER
    )))

    rows = rows.scalars().all()
    rows = db_objects_to_schema(rows, ShopUnit)
    return rows


def db_object_to_schema(db_obj, schema):
    return schema.from_orm(db_obj)


def db_objects_to_schema(db_objs, schema):
    res = []
    for obj in db_objs:
        res.append(db_object_to_schema(obj, schema))
    return res

# async def get_biggest_cities(session: AsyncSession) -> list[City]:
#     result = await session.execute(select(City).order_by(City.population.desc()).limit(20))
#     return result.scalars().all()
#
#
# def add_city(session: AsyncSession, name: str, population: int):
#     new_city = City(name=name, population=population)
#     session.add(new_city)
#     return new_city
