"""Render every app page through Streamlit's test harness and fail on any exception."""

from streamlit.testing.v1 import AppTest

PAGES = ["Model comparison", "Why the best model", "Review queue", "FP-Growth & patterns"]


def check(page: str) -> None:
    at = AppTest.from_file("app.py", default_timeout=120).run()
    if at.exception:
        raise AssertionError(f"{page}: initial run raised {at.exception[0].value}")
    at.sidebar.radio[0].set_value(page).run()
    if at.exception:
        raise AssertionError(f"{page}: {at.exception[0].value}")
    print(f"OK  {page}")


def sweep_cutoff() -> None:
    at = AppTest.from_file("app.py", default_timeout=120).run()
    at.sidebar.radio[0].set_value("Review queue").run()
    for value in (0.10, 0.50, 0.90, 0.99):
        # Re-acquire each pass: reusing a widget handle across runs leaves a stale
        # session-state key behind.
        slider = next(w for w in at.slider if "probability" in w.label.lower())
        slider.set_value(value).run()
        if at.exception:
            raise AssertionError(f"cutoff {value}: {at.exception[0].value}")
        print(f"OK  Review queue @ cutoff {value}")


for name in PAGES:
    check(name)
sweep_cutoff()
print("all pages render clean")