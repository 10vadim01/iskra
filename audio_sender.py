import nest_asyncio
nest_asyncio.apply()

# ... rest of your imports ...

# ... rest of your code ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6996)
