# Initialize Dynaconf
from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["config/config.yaml"],
    load_dotenv=True,
    environments=True,
)
