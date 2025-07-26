from src.presentation.rest.app import create_app

# ----------------------------------------------------------------------------
app = create_app()



# ----------------------------------------------------------------------------
@app.get('/')
def status():
    return {"Status": "Working!"}
