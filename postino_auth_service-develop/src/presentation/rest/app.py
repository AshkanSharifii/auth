from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.di.container import Container
from src.presentation.rest.routers import routes


# ----------------------------------------------------------------------------
def create_app():
    app = FastAPI(title="Postino", default_response_class=ORJSONResponse, root_path="/user")

    # Add CORS middleware
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["http://localhost:3001", "https://api.techchain.co"],
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    # Add routes to FastAPI
    app.include_router(routes)

    # Init container resources
    container = Container()
    container.init_resources()
    app.container = container

    return app
