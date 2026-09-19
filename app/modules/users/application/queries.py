from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GetProfileQuery:
    user_id: UUID


@dataclass(frozen=True, slots=True)
class GetPreferencesQuery:
    user_id: UUID


@dataclass(frozen=True, slots=True)
class ExportPersonalDataQuery:
    user_id: UUID
