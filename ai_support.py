CONDITION_RULES = {

    "Common Cold": ["cold", "cough"],

    "Viral Fever": ["fever", "fatigue", "body pain"],

    "Migraine": ["headache", "nausea"],

    "Food Poisoning": ["vomiting", "nausea", "stomach pain"]

}


DANGER_SYMPTOMS = [

    "chest pain",

    "shortness of breath",

    "severe bleeding",

    "loss of consciousness"

]


SEVERITY_RULES = {

    "HIGH": DANGER_SYMPTOMS + [

        "difficulty breathing"

    ],

    "MEDIUM": [

        "high fever",

        "persistent vomiting",

        "severe pain"

    ],

    "LOW": [

        "fever",

        "headache",

        "cold",

        "cough"

    ]

}


def ai_medical_support(symptoms):

    symptoms = {

        str(symptom).strip().lower()

        for symptom in (symptoms or [])

    }

    possible_conditions = []

    for condition, keywords in CONDITION_RULES.items():

        if symptoms.intersection(keywords):

            possible_conditions.append(condition)

    if symptoms.intersection(SEVERITY_RULES["HIGH"]):

        severity = "HIGH"

    elif symptoms.intersection(SEVERITY_RULES["MEDIUM"]):

        severity = "MEDIUM"

    elif symptoms.intersection(SEVERITY_RULES["LOW"]):

        severity = "LOW"

    else:

        severity = "UNKNOWN"

    return {

        "severity": severity,

        "possible_conditions": possible_conditions,

        "medicines": [],

        "urgent_warning": (

            "Emergency symptoms detected. Seek urgent medical care."

            if symptoms.intersection(DANGER_SYMPTOMS)

            else None

        ),

        "disclaimer": (

            "Clinical support prototype only. "

            "Not a diagnosis or prescription."

        )

    }