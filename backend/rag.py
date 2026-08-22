def build_rag_context(
    user_query,
    nlp_analysis,
    health_information,
    related_concepts
):
    context = []

    context.append(
        f"USER QUESTION:\n{user_query}"
    )

    if nlp_analysis:
        context.append(
            f"""
MEDICAL NLP ANALYSIS:

Disease:
{nlp_analysis.get("disease")}

Intent:
{nlp_analysis.get("intent")}

Symptoms:
{nlp_analysis.get("symptoms")}
"""
        )

    if health_information:
        context.append(
            "\nTRUSTED MEDICAL KNOWLEDGE:\n"
        )

        for item in health_information:
            context.append(
                f"""
Disease:
{item.get("disease")}

Information:
{item.get("information")}
"""
            )

    if related_concepts:
        context.append(
            "\nMEDICAL KNOWLEDGE GRAPH:\n"
        )

        for concept in related_concepts:
            context.append(str(concept))

    return "\n".join(context)