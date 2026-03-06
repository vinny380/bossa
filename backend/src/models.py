from pydantic import BaseModel


class FileCreate(BaseModel):
    path: str
    content: str


class FileRead(BaseModel):
    path: str
    content: str


class LsEntry(BaseModel):
    name: str
    is_directory: bool


class GrepResult(BaseModel):
    path: str
    line_number: int
    line: str


class GrepSearchRequest(BaseModel):
    pattern: str
    path: str = "/"
