import re


SYMPTOMS = [

    "shortness of breath",

    "chest pain",

    "high fever",

    "stomach pain",

    "body pain",

    "headache",

    "fatigue",

    "fever",

    "cough",

    "cold",

    "nausea",

    "vomiting",

    "pain"

]


MEDICINES = [

    "paracetamol",

    "aspirin",

    "ibuprofen",

    "amoxicillin",

    "cetirizine"

]


def contains_phrase(text, phrase):

    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"

    return re.search(pattern, text) is not None


def extract_medical_info(text):

    text = (text or "").lower()

    symptoms_found = [

        symptom

        for symptom in SYMPTOMS

        if contains_phrase(text, symptom)

    ]

    medicines_found = [

        medicine

        for medicine in MEDICINES

        if contains_phrase(text, medicine)

    ]

    specific_pain = [

        "chest pain",

        "body pain",

        "stomach pain"

    ]

    if any(item in symptoms_found for item in specific_pain):

        symptoms_found = [

            item

            for item in symptoms_found

            if item != "pain"

        ]

    return {

        "symptoms": sorted(set(symptoms_found)),

        "medicines": sorted(set(medicines_found))

    }


if __name__ == "__main__":

    sample = "Patient reports fever and headache."

    print(extract_medical_info(sample))