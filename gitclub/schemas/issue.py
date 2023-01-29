from pydantic import BaseModel


class IssueInsert(BaseModel):
    title: str
    closed: bool
    repository_id: int
    creator_id: int


class IssueInfo(IssueInsert):
    id: int
