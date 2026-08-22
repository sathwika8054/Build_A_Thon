from medical_nlp import extract_medical_concepts


questions = [
    "What are the symptoms of dengue?",
    "How can I prevent malaria?",
    "How does influenza spread?",
    "What are the warning signs of dengue?",
    "What treatment is available for malaria?"
]


for question in questions:

    result = extract_medical_concepts(question)

    print("\nQuestion:", question)
    print("Disease:", result["disease"])
    print("Intent:", result["intent"])
    print("Symptoms:", result["symptoms"])