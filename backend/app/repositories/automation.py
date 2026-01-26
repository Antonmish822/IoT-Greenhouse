from sqlmodel import Session, select

from ..models import AutomationSetting


def get_for_greenhouse(session: Session, greenhouse_id: int) -> AutomationSetting | None:
    statement = select(AutomationSetting).where(AutomationSetting.greenhouse_id == greenhouse_id)
    return session.exec(statement).first()


def list_all(session: Session) -> list[AutomationSetting]:
    statement = select(AutomationSetting)
    return session.exec(statement).all()


def save(session: Session, setting: AutomationSetting) -> AutomationSetting:
    session.add(setting)
    session.commit()
    session.refresh(setting)
    return setting
