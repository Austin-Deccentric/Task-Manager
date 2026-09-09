from typing import Annotated

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel


def verify_api_key(x_api_key: Annotated[str, Header()]):
    if x_api_key != "my_api_key":
        raise HTTPException(status_code=401, detail="Invalid API Key")

api_dep = Depends(verify_api_key)

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 10

# Todo include filter by status for Tasks