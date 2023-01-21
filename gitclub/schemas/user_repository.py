from pydantic import BaseModel


class UserRepositoryInfo(BaseModel):
    user_id: int
    repository_id: int
    role: str
