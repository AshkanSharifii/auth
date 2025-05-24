from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form
from dependency_injector.wiring import Provide, inject
from typing import Annotated, Optional
from uuid import UUID

from src.domain.entities.brand import Brand
from src.domain.exceptions import (BrandExists, BrandNotFound, 
                                   ObjStorageClientError, IndustryNotFound, 
                                   ToneNotFound, InvalidHexColorCode)
from src.presentation.rest.user.dependencies import get_current_user
from src.di.container import Container


router = APIRouter()


@router.get('/', status_code=status.HTTP_200_OK)
async def user_brands_list(
    user_data: tuple = Depends(get_current_user)):

    user, role, brands = user_data

    return brands


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=Brand)
@inject
async def create_user_brand(
    brand_logo: UploadFile,
    brand_name: Annotated[str, Form(max_length=100)],
    brand_desc: Annotated[str, Form(min_length=10, max_length=500)],
    brand_tone: Annotated[UUID, Form()],
    brand_industry: Annotated[UUID, Form()],
    brand_slogan: Annotated[Optional[str], Form(max_length=100)] = None,
    brand_audience: Annotated[Optional[str], Form(max_length=100)] = None,
    brand_color: Annotated[Optional[str], Form(max_length=7)] = None,
    user_data: tuple = Depends(get_current_user),
    create_user_brand_use_case = Depends(Provide[Container.create_user_brand_use_case_provider])):

    user, role, brands = user_data

    try:
        brand = await create_user_brand_use_case.execute(
            user.id, brand_name, brand_logo,
            brand_desc, brand_tone, brand_industry,
            brand_slogan, brand_audience, brand_color
        )
        return brand
    
    except InvalidHexColorCode as invalid_color:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(invalid_color)
        )
    
    except ToneNotFound as tone_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(tone_not_found)
        )
    
    except IndustryNotFound as industry_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(industry_not_found)
        )

    except ObjStorageClientError as client_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(client_error)
        )

    except BrandExists as exist_brand:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exist_brand)
        )


@router.put('/update', status_code=status.HTTP_200_OK, response_model=Brand)
@inject
async def update_user_brand(
    brand_id: UUID,
    brand_logo: UploadFile,
    brand_name: Annotated[str, Form(max_length=100)],
    brand_desc: Annotated[str, Form(min_length=10, max_length=500)],
    brand_tone: Annotated[UUID, Form()],
    brand_industry: Annotated[UUID, Form()],
    brand_slogan: Annotated[Optional[str], Form(max_length=100)] = None,
    brand_audience: Annotated[Optional[str], Form(max_length=100)] = None,
    brand_color: Annotated[Optional[str], Form(max_length=7)] = None,
    user_data: tuple = Depends(get_current_user),
    update_user_brand_use_case = Depends(Provide[Container.update_user_brand_use_case_provicer])):

    user, role, brands = user_data

    try:
        brand = await update_user_brand_use_case.execute(
            brand_id, user.id, brand_name, brand_logo,
            brand_desc, brand_tone, brand_industry,
            brand_slogan, brand_audience, brand_color
        )
        return brand
    
    except InvalidHexColorCode as invalid_color:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(invalid_color)
        )
    
    except ToneNotFound as tone_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(tone_not_found)
        )
    
    except IndustryNotFound as industry_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(industry_not_found)
        )
    
    except ObjStorageClientError as client_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(client_error)
        )

    except BrandNotFound as exist_brand:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exist_brand)
        )


@router.delete('/delete', status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_user_brand(
    brand_id: UUID,
    user_data: tuple = Depends(get_current_user),
    delete_user_brand_use_case = Depends(Provide[Container.delete_user_brand_use_case_provicer])):

    user, role, brands = user_data

    try:
        await delete_user_brand_use_case.execute(brand_id, user.id)
        
    except ObjStorageClientError as client_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(client_error)
        )

    except BrandNotFound as brand_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(brand_not_found)
        )
    