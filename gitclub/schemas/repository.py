from pydantic import BaseModel


class RepositoryInsert(BaseModel):
    name: str
    organization_id: int


class RepositoryInfo(RepositoryInsert):
    id: int
