from pydantic import BaseModel


class UserOrganizationInfo(BaseModel):
    user_id: int
    organization_id: int
    role: str
