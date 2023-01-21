from pydantic import BaseModel


class OrganizationInsert(BaseModel):
    name: str
    base_repo_role: str
    billing_address: str


class OrganizationInfo(OrganizationInsert):
    id: int
