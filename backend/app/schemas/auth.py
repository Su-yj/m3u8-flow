from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")
