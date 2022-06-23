from datetime import datetime
from enum import Enum
from typing import Union, List
import json


from fastapi import FastAPI, Request, Query, Path, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import ValidationError
from fastapi.exception_handlers import RequestValidationError, HTTPException

from pydantic import BaseModel, validator, root_validator

from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas import (ShopUnit, ShopUnitImportRequest, ShopSalesRequest, ShopUnitStatisticsRequest,
                         ShopUnitStatisticsResponse, Error)
from app.db.db import get_session
from app.service import (get_shop_unit, import_shop_units, delete_shop_unit, get_unit_statistics, get_sales,
                         recount_prices)


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def exception_handler(request: Request, exc: RequestValidationError):
    print('RequestValidationError', request, exc)
    error = Error(code=400, message="Validation Failed")
    return JSONResponse(status_code=400, content=error.dict())


@app.exception_handler(HTTPException)
async def exception_handler(request: Request, exc: HTTPException):
    status_code = exc.status_code
    details = exc.detail
    print(f'HTTPException {status_code}: {details}')

    if status_code == 400:
        error = Error(code=400, message="Validation Failed")
        return JSONResponse(status_code=400, content=error.dict())
    elif status_code == 404:
        error = Error(code=404, message="Item not found")
        return JSONResponse(status_code=404, content=error.dict())


@app.post('/imports', tags=['Basic'])
async def imports(rq: ShopUnitImportRequest, db: AsyncSession = Depends(get_session)):
    """
    # hello
    it is docs!!
    """
    await import_shop_units(db, rq)
    await recount_prices(db, rq.items)

    return JSONResponse(dict(code=200, message=f"Success for 'imports' ({len(rq.items)} items)"))


@app.delete('/delete/{id}', tags=['Basic'])
async def delete(id: str, db: AsyncSession = Depends(get_session)):
    res = await delete_shop_unit(db, id)
    if not res:
        raise HTTPException(404, "Item not found")
    return dict(code=200, message=f"Success for 'delete' (id: {id})")


@app.get('/nodes/{id}', tags=['Basic'], responses={200: {'model': ShopUnit}, 404: {'model': Error}})
async def nodes(id: str, db: AsyncSession = Depends(get_session)):
    res = await get_shop_unit(db, id, children=True)
    if res:
        return res[0]
    else:
        raise HTTPException(404)


@app.get('/sales', tags=['Extra'], responses={200: {'model': ShopUnitStatisticsResponse}})
async def sales(rq: ShopSalesRequest, db: AsyncSession = Depends(get_session)):
    res = await get_sales(db, rq.date)
    return res


@app.get('/node/{id}/statistics', tags=['Extra'], responses={200: {'model': ShopUnitStatisticsResponse}})
async def statistics(id: str, rq: ShopUnitStatisticsRequest, db: AsyncSession = Depends(get_session)):
    if not get_shop_unit(db, id):
        raise HTTPException(404)
    res = await get_unit_statistics(db, id, rq.dateStart, rq.dateEnd)
    return res
