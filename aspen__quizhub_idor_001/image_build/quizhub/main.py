from fastapi import FastAPI

from quizhub.db import reset_state
from quizhub.routers import attempts, quiz_bank, quizzes


def create_app() -> FastAPI:
    reset_state()
    app = FastAPI(title="quizhub")
    app.include_router(quiz_bank.router)
    app.include_router(quizzes.router)
    app.include_router(attempts.router)
    return app


app = create_app()
