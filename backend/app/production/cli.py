import json

from app.production.database import Base, SessionLocal, engine
from app.production.seed import seed_mvp_demo


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as session:
        print(json.dumps(seed_mvp_demo(session), indent=2))


if __name__ == "__main__":
    main()
