import pandas as pd

from telecom_intelligence.nlp.classify_complaints import (
    classify_support_tickets,
    normalize_label,
)


class FakeClassifier:
    def __call__(self, text, candidate_labels, multi_label=False):
        if "cancel" in text.lower():
            return {"labels": ["cancellation request"], "scores": [0.91]}

        return {"labels": ["billing"], "scores": [0.82]}


def test_normalize_label_converts_spaces_to_snake_case() -> None:
    assert normalize_label("Cancellation Request") == "cancellation_request"
    assert normalize_label("slow internet") == "slow_internet"


def test_classify_support_tickets_adds_prediction_columns() -> None:
    tickets = pd.DataFrame(
        [
            {
                "ticket_id": "tic_1",
                "customer_id": "cust_1",
                "ticket_text": "I want to cancel my service.",
                "complaint_category_seed": "cancellation_request",
            },
            {
                "ticket_id": "tic_2",
                "customer_id": "cust_2",
                "ticket_text": "My bill is too high.",
                "complaint_category_seed": "billing",
            },
        ]
    )

    classified = classify_support_tickets(tickets, FakeClassifier())

    assert classified["complaint_category_predicted"].tolist() == [
        "cancellation_request",
        "billing",
    ]
    assert classified["complaint_category_score"].tolist() == [0.91, 0.82]
    assert classified["complaint_category_matches_seed"].tolist() == [True, True]
