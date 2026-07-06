import uvicorn

uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8018,
    reload=False
)