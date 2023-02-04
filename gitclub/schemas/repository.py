from pydantic import BaseModel


class RepositoryInsert(BaseModel):
    name: str


class RepositoryInsert2(RepositoryInsert):
    organization_id: int


class RepositoryInfo(RepositoryInsert2):
    id: int
