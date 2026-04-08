from typing import TYPE_CHECKING

from tortoise.contrib.pydantic import PydanticModel, pydantic_model_creator

from app.models import GlobalConfig

if TYPE_CHECKING:

    class GlobalConfigPydantic(GlobalConfig, PydanticModel):  # pyright: ignore[reportGeneralTypeIssues]
        pass

    class GlobalConfigUpdatePydantic(GlobalConfig, PydanticModel):  # pyright: ignore[reportGeneralTypeIssues]
        pass

else:
    GlobalConfigPydantic = pydantic_model_creator(GlobalConfig, name="GlobalConfig")
    GlobalConfigUpdatePydantic = pydantic_model_creator(
        GlobalConfig, name="GlobalConfigUpdate", exclude_readonly=True
    )
