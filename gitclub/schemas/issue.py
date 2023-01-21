from pydantic import BaseModel


class IssueInsert(BaseModel):
    name: str
    organization_id: int


class IssueInfo(IssueInsert):
    id: int
