from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class DraftProfile(StrictModel):
    condition: str = Field(default='', max_length=160)
    stage: str = Field(default='', max_length=80)
    biomarkers: list[str] = Field(default_factory=list, max_length=12)
    city: str = Field(default='', max_length=100)


class Profile(DraftProfile):
    condition: str = Field(min_length=3, max_length=160)


class Question(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    question: str = Field(min_length=1, max_length=700)


class PreparedQuery(StrictModel):
    status: Literal['ready', 'needs_details', 'off_topic']
    profile: DraftProfile
    guide: list[Question] = Field(max_length=5)

    @model_validator(mode='after')
    def enforce_preparation_state(self):
        if self.status == 'ready' and len(self.profile.condition) < 3:
            self.status = 'needs_details'
        if self.status != 'ready':
            # An unrelated request cannot carry a model-invented search profile.
            self.profile = DraftProfile()
            self.guide = []
        elif len(self.guide) != 5:
            raise ValueError('A ready search requires five discussion questions.')
        return self


class Extraction(StrictModel):
    note: str = Field(min_length=3, max_length=6000)
    consent: bool = False


class Search(StrictModel):
    profile: Profile
    consent: bool = False
