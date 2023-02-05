from pydantic import BaseModel


class IssueInsert(BaseModel):
    title: str
    closed: bool = False
    repository_id: int
    creator_id: int


class IssuePatch(BaseModel):
    title: str | None
    closed: bool | None
    creator_id: int | None


class IssueInfo(IssueInsert):
    id: int
