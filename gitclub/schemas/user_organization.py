from pydantic import BaseModel


class UserOrganizationInfo(BaseModel):
    user_id: int
    repository_id: int
    role: str
