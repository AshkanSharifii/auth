from ..conftest import client

import pytest
    

@pytest.mark.asyncio
async def test_status(client):
    response = await client.get('/')
    assert response.status_code == 200
    assert response.json() == {"Status": "Working!"}
    