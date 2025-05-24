from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from dependency_injector.wiring import Provide, inject

from src.domain.entities.industry import BrandIndustry
from src.domain.exceptions import IndustryNotFound
from src.di.container import Container
from src.presentation.rest.user.dependencies import get_current_user
from src.application.dtos.brand_industry_dto import BarndIndustryDto


router = APIRouter()

@router.get('/', response_model=list[BrandIndustry], status_code=status.HTTP_200_OK)
@inject
async def brand_industries_list(
    user_data: tuple = Depends(get_current_user),
    industries_list_use_case = Depends(Provide[Container.get_brand_industries_use_case])):

    return await industries_list_use_case.execute()


@router.post('/', response_model=BrandIndustry, status_code=status.HTTP_201_CREATED)
@inject
async def brand_industry_create(
    industry: BarndIndustryDto,
    user_data: tuple = Depends(get_current_user),
    create_industry = Depends(Provide[Container.create_brand_industry_use_case])
    ):

    user, role, brands = user_data
    
    try:
        industry = await create_industry.execute(
            industry.name,
            industry.description,
            user.role_id
        )
        return industry
    
    except PermissionError as perm_error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_error)
        )
    
    
@router.put('/update', response_model=BrandIndustry, status_code=status.HTTP_200_OK)
@inject
async def brand_industry_update(
    industry_id: UUID,
    industry: BarndIndustryDto,
    user_data: tuple = Depends(get_current_user),
    update_industry = Depends(Provide[Container.update_brand_industry_use_case])
    ):

    user, role, brands = user_data
    
    try:
        industry = await update_industry.execute(
            industry_id,
            industry.name,
            industry.description,
            user.role_id
        )
        return industry
    
    except PermissionError as perm_error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_error)
        )
    
    except IndustryNotFound as industry_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(industry_not_found)
        )


@router.delete('/delete', status_code=status.HTTP_204_NO_CONTENT)
@inject
async def brand_industry_delete(
    industry_id: UUID,
    user_data: tuple = Depends(get_current_user),
    delete_industry = Depends(Provide[Container.delete_brand_industry_use_case])
    ):

    user, role, brands = user_data
    
    try:
        await delete_industry.execute(
            industry_id,
            user.role_id
        )
    
    except PermissionError as perm_error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_error)
        )
    
    except IndustryNotFound as industry_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(industry_not_found)
        )
    