# --------------------------------
# Document processing decision
# --------------------------------

def make_processing_decision(
    quality_result: dict,
    relevance_result: dict,
) -> dict:
    """
    Combine document quality and relevance results
    into one processing decision.
    """

    # --------------------------------
    # 1. Quality failed
    # --------------------------------

    if quality_result["quality_status"] == "DO_NOT_PROCESS":

        return {
            "processing_status": "DO_NOT_PROCESS",
            "reason": quality_result["reason"],
            "manual_review_required": True,
        }

    # --------------------------------
    # 2. Document is not relevant
    # --------------------------------

    if not relevance_result["relevant"]:

        return {
            "processing_status": "DO_NOT_PROCESS",
            "reason": relevance_result["reason"],
            "manual_review_required": True,
        }

    # --------------------------------
    # 3. Document can be processed
    # --------------------------------

    return {
        "processing_status": "PROCESS",
        "reason": "Document passed quality and relevance checks",
        "manual_review_required": False,
    }