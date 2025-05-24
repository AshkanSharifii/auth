from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from dependency_injector.wiring import Provide, inject

from src.domain.entities.tone import BrandTone
from src.di.container import Container
from src.domain.exceptions import ToneNotFound
from src.presentation.rest.user.dependencies import get_current_user
from src.application.dtos.brand_tone_dto import BarndToneDto


router = APIRouter()


@router.get('/', response_model=list[BrandTone], status_code=status.HTTP_200_OK)
@inject
async def brand_tones_list(
    user_data: tuple = Depends(get_current_user),
    tones_list_use_case = Depends(Provide[Container.get_brand_tones_use_case])):

    return await tones_list_use_case.execute()


@router.post('/', response_model=BrandTone, status_code=status.HTTP_201_CREATED)
@inject
async def brand_tone_create(
    tone: BarndToneDto,
    user_data: tuple = Depends(get_current_user),
    create_tone_use_case = Depends(Provide[Container.create_brand_tone_use_case])):

    user, role, brands = user_data
    
    try:
        tone = await create_tone_use_case.execute(
            tone.name,
            tone.description,
            user.role_id
        )
        return tone
    
    except PermissionError as perm_error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_error)
        )


@router.put('/update', response_model=BrandTone, status_code=status.HTTP_200_OK)
@inject
async def brand_tone_update(
    tone_id: UUID,
    tone: BarndToneDto,
    user_data: tuple = Depends(get_current_user),
    update_tone_use_case = Depends(Provide[Container.update_brand_tone_use_case])
    ):

    user, role, brands = user_data
    
    try:
        tone = await update_tone_use_case.execute(
            tone_id,
            tone.name,
            tone.description,
            user.role_id
        )
        return tone
    
    except PermissionError as perm_error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_error)
        )
    
    except ToneNotFound as tone_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(tone_not_found)
        )
    

@router.delete('/delete', status_code=status.HTTP_204_NO_CONTENT)
@inject
async def brand_tone_delete(
    tone_id: UUID,
    user_data: tuple = Depends(get_current_user),
    delete_tone_use_case = Depends(Provide[Container.delete_brand_tone_use_case])
    ):

    user, role, brands = user_data
    
    try:
        await delete_tone_use_case.execute(
            tone_id,
            user.role_id
        )
    
    except PermissionError as perm_error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_error)
        )
    
    except ToneNotFound as tone_not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(tone_not_found)
        )
    