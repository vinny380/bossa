from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Tier(str, Enum):
    """Account tier. Owner bypasses all usage limits."""

    FREE = "free"
    PRO = "pro"
    OWNER = "owner"


class FileCreate(BaseModel):
    path: str
    content: str


class FileEdit(BaseModel):
    path: str
    old_string: str
    new_string: str
    replace_all: bool = False


class FileBulkCreate(BaseModel):
    files: list[FileCreate]


class FileBulkCreateResponse(BaseModel):
    created: int
    updated: int
    failed: list[dict]


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
    pattern: str | None = None
    path: str = "/"
    regex: bool = False
    case_sensitive: bool = False
    whole_word: bool = False
    max_matches: int = 100
    offset: int = 0
    output_mode: Literal["matches", "files_with_matches", "count"] = "matches"
    all_of: list[str] = Field(default_factory=list)
    any_of: list[str] = Field(default_factory=list)
    none_of: list[str] = Field(default_factory=list)
    context_before: int = 0
    context_after: int = 0

    @model_validator(mode="after")
    def validate_search_terms(self) -> "GrepSearchRequest":
        if (
            self.pattern is None
            and not self.all_of
            and not self.any_of
            and not self.none_of
        ):
            raise ValueError("At least one search criterion is required.")
        if self.max_matches < 1:
            raise ValueError("max_matches must be at least 1.")
        if self.offset < 0:
            raise ValueError("offset must be 0 or greater.")
        if self.context_before < 0 or self.context_after < 0:
            raise ValueError("context_before and context_after must be 0 or greater.")
        return self


class GrepMatch(BaseModel):
    path: str
    line_number: int
    line: str
    context_before: list[str] = Field(default_factory=list)
    context_after: list[str] = Field(default_factory=list)


class GrepSearchResponse(BaseModel):
    output_mode: Literal["matches", "files_with_matches", "count"]
    matches: list[GrepMatch] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    count: int = 0
    total_matches: int = 0
    returned_matches: int = 0
    has_more: bool = False
    next_offset: int | None = None


class BatchOp(BaseModel):
    op: Literal["read", "write", "delete"]
    path: str
    content: str | None = None

    @model_validator(mode="after")
    def validate_write_has_content(self) -> "BatchOp":
        if self.op == "write" and self.content is None:
            raise ValueError("content required for write op")
        return self


class BatchRequest(BaseModel):
    ops: list[BatchOp]
