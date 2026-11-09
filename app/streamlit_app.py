"""Loan default review dashboard entrypoint."""

from components.common import apply_theme, load_features, sidebar
from views.data_leakage import data_page
from views.data_model import data_model_page
from views.models import models_page
from views.patterns import patterns_page
from views.portfolio import portfolio_page
from views.simulator import simulator_page

VIEWS = {
    "Executive overview": portfolio_page,
    "Data & leakage": data_page,
    "Models": models_page,
    "Patterns": patterns_page,
    "Simulator": simulator_page,
    "Data model card": data_model_page,
}


def main() -> None:
    apply_theme()
    features = load_features()
    page = sidebar(features)
    VIEWS[page]()


if __name__ == "__main__":
    main()
