from datetime import datetime
from enum import Enum
from typing import Union, List
from uuid import UUID

from fastapi.exceptions import ValidationError, HTTPException
from pydantic import BaseModel, validator, root_validator

DATETIME_ISO_8601_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DATE_FIELDS = ('date', 'dateStart', 'dateEnd', 'updateDate')


def convert_datetime_to_iso_8601_with_z_suffix(dt: datetime) -> str:
    return dt.strftime(DATETIME_ISO_8601_FORMAT)


class BaseModelExt(BaseModel):
    @validator(*DATE_FIELDS, check_fields=False, pre=True)
    def dates_validator(cls, value):
        if isinstance(value, datetime):
            return value
        res = datetime.strptime(value, DATETIME_ISO_8601_FORMAT)
        return res

    class Config:
        json_encoders = {
            datetime: convert_datetime_to_iso_8601_with_z_suffix
        }
        orm_mode = True


class ShopUnitType(str, Enum):
    OFFER = 'OFFER'
    CATEGORY = 'CATEGORY'


class ShopUnit(BaseModelExt):
    id: str
    name: str
    date: datetime
    parentId: str = None
    type: ShopUnitType
    price: int = None
    children: List['ShopUnit'] = None


ShopUnit.update_forward_refs()


class ShopUnitImport(BaseModelExt):
    id: str
    name: str
    parentId: str = None
    type: ShopUnitType
    price: int = None

    @root_validator()
    def check(cls, values):
        if values["type"] == ShopUnitType.OFFER and values['price'] is None:
            raise HTTPException(400, f"Price should be set in OFFER!")
        return values


class ShopUnitImportRequest(BaseModelExt):
    items: List[ShopUnitImport]
    updateDate: datetime

    @validator('items')
    def check_items(cls, values):
        ids = []
        for item in values:
            if item.id not in ids:
                ids.append(item.id)
            else:
                raise HTTPException(400, f"The same ID in 'ShopUnitImportRequest' (ID: {item.id})")
        return values


class ShopUnitStatisticsRequest(BaseModelExt):
    dateStart: datetime = None
    dateEnd: datetime = None

    @root_validator()
    def check_values(cls, values):
        if values['dateStart'] and values['dateEnd']:
            if values['dateEnd'] < values['dateStart']:
                raise HTTPException(400, "Field 'dateEnd' should be grater than 'dateStart'")

        return values


class ShopSalesRequest(BaseModelExt):
    date: datetime


class ShopUnitStatistics(BaseModelExt):
    id: str
    name: str
    date: datetime
    parentId: str = None
    type: ShopUnitType
    price: int = None


class ShopUnitStatisticsResponse(BaseModelExt):
    items: List[ShopUnitStatistics]


class Error(BaseModel):
    code: int
    message: str

