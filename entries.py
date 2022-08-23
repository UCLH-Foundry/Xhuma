import uuid
from ast import expr_context

from fhirclient.models import allergyintolerance, coding, condition
from fhirclient.models import medication as fhirmed
from fhirclient.models import medicationstatement


def generate_code(coding: coding.Coding) -> dict:
    code = {
        "@code": coding.code,
        "@displayName": coding.display,
        "@codeSystemName": coding.system,
    }

    return code


def medication(entry: medicationstatement.MedicationStatement, index: dict) -> dict:
    # http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.42.html

    med = {
        "substanceAdministration": {
            "@classCode": "SBADM",
            "@moodCode": "INT",
        }
    }

    med["substanceAdministration"]["templateID"] = {
        "@root": "2.16.840.1.113883.10.20.22.4.42",
        "@extension": "2014-06-09",
    }
    med["substanceAdministration"]["id"] = {"@root": entry.identifier[0].value}
    med["substanceAdministration"]["code"] = {
        "@code": "CONC",
        "@codesystem": "2.16.840.1.113883.5.6",
    }

    med["substanceAdministration"]["statuscode"] = {"@code": entry.status}

    # TODO add robust checking on this in case there's no high value
    med["substanceAdministration"]["effectTime"] = {
        "low": {"@value": entry.effectivePeriod.start.isostring},
        "high": {"@value": entry.effectivePeriod.end.isostring},
    }

    referenced_med: fhirmed.Medication() = index[entry.medicationReference.reference]
    print(referenced_med.code.coding)
    request = index[entry.basedOn[0].reference]

    # medication information
    # http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.23.html
    med["substanceAdministration"]["consumable"] = {}
    med["substanceAdministration"]["consumable"]["manufacturedProduct"] = {
        "@classCode": "MANU",
        "templateID": {
            "@root": "2.16.840.1.113883.10.20.22.4.23",
            "@extension": "2014-06-09",
            "manufacturedMaterial": {
                "code": [generate_code(x) for x in referenced_med.code.coding],
            },
        },
    }

    med["substanceAdministration"]["entryRelationship"] = {
        "@typeCode": "SUBJ",
        "act": {
            "@classCode": "ACT",
            "@moodCode": "INT",
            "templateID": {
                "@root": "2.16.840.1.113883.10.20.22.4.20",
                "@extension": "2014-06-09",
            },
            "code": {
                "@code": "422037009",
                "@displayName": "Provider medication administration instructions",
                "@codeSystemName": "SNOMED CT",
                "@codeSystem": "2.16.840.1.113883.6.96",
            },
            "text": {"#text": entry.dosage[0].text},
            "patientInstruction": {"#text": entry.dosage[0].patientInstruction},
            "satusCode": {"@code": "completed"},
        },
    }

    return med


def problem(entry: condition.Condition) -> dict:
    # http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.3.html
    prob = {
        "act": {
            "@classCode": "ACT",
            "@moodCode": "EVN",
        }
    }

    prob["act"]["templateID"] = {
        "@root": "2.16.840.1.113883.10.20.22.4.3",
        "@extension": "2015-08-01",
    }
    prob["act"]["id"] = {"@root": uuid.uuid4()}
    prob["act"]["code"] = {"@code": "CONC", "@codesystem": "2.16.840.1.113883.5.6"}

    prob["act"]["statuscode"] = {"@code": entry.clinicalStatus}
    prob["act"]["effectTime"] = {"low": {"@value": entry.assertedDate.isostring}}
    prob["act"]["entryRelationship"] = {"@typeCode": "SUBJ"}

    # http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.4.html
    observation = {"@classCode": "OBS", "@moodCode": "EVN"}
    observation["templateId"] = {
        "@root": "2.16.840.1.113883.10.20.22.4.4",
        "@extension": "2015-08-01",
    }
    observation["id"] = {"@root": uuid.uuid4()}
    observation["code"] = [
        {
            "@code": "64572001",
            "@displayName": "Condition",
            "@codeSystemName": "SNOMED CT",
            "@codeSystem": "2.16.840.1.113883.6.96",
        },
        {
            "@code": "75323-6",
            "@displayName": "Condition",
            "@codeSystemName": "LOINC",
            "@codeSystem": "2.16.840.1.113883.6.1",
        },
    ]
    observation["statusCode"] = {"@code": "completed"}
    observation["effectiveTime"] = {"low": {"@value": entry.assertedDate.isostring}}
    observation["value"] = {
        "@xsi:type": "CD",
        "@code": entry.code.coding[0].code,
        "@displayName": entry.code.coding[0].display,
        "@codeSystemName": "SNOMED CT",
        "@codeSystem": "2.16.840.1.113883.6.96",
    }

    prob["act"]["entryRelationship"]["observation"] = observation

    return prob


def allergy(entry: allergyintolerance.AllergyIntolerance) -> dict:
    # http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.30.html
    all = {
        "act": {
            "@classCode": "ACT",
            "@moodCode": "EVN",
        }
    }
    all["act"]["templateID"] = {
        "@root": "2.16.840.1.113883.10.20.22.4.30",
        "@extension": "2015-08-01",
    }
    all["act"]["id"] = {"@root": uuid.uuid4()}
    all["act"]["code"] = {"@code": "CONC", "@codesystem": "2.16.840.1.113883.5.6"}

    # may need to be made dynamic if force to query old allergies
    all["act"]["statuscode"] = {"@code": "active"}
    all["act"]["effectTime"] = {"low": {"@value": entry.assertedDate.isostring}}
    all["act"]["entryRelationship"] = {"@typeCode": "SUBJ"}

    # http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.7.html
    observation = {"@classCode": "OBS", "@moodCode": "EVN"}
    observation["templateId"] = {
        "@root": "2.16.840.1.113883.10.20.22.4.7",
        "@extension": "2014-06-09",
    }
    observation["id"] = {"@root": uuid.uuid4()}
    observation["code"] = {"@code": "ASSERTION", "@codeSystem": "2.16.840.1.113883.5.4"}
    observation["statusCode"] = {"@code": "completed"}
    observation["value"] = {
        "@xsi:type": "CD",
        "@code": "416098002",
        "@displayName": "drug allergy",
        "@codeSystemName": "SNOMED CT",
        "@codeSystem": "2.16.840.1.113883.6.96",
    }

    observation["participant"] = {
        "@typeCode": "CSM",
        "participantRole": {
            "@classCode": "MANU",
            "playingEntity": {
                "@classCode": "MMAT",
                "code": {
                    "@code": entry.code.coding[0].code,
                    "@displayName": entry.code.coding[0].display,
                    "@codeSystemName": "SNOMED CT",
                    "@codeSystem": "2.16.840.1.113883.6.96",
                },
            },
        },
    }

    observation["entryRelationship"] = {
        "@typeCode": "MSFT",
        "@inversionInd": "true",
        "observation": {
            "@classCode": "OBS",
            "@moodCode": "EVN",
            "templateID": {
                "@root": "2.16.840.1.113883.10.20.22.4.9",
                "@extension": "2014-06-09",
            },
            "id": {"@root": uuid.uuid4()},
            "code": {"@code": "ASSERTION", "@codeSystem": "2.16.840.1.113883.5.4"},
            "effectiveTime": {"low": {"@value": entry.assertedDate.isostring}},
            "value": {
                "@xsi:type": "CD",
                "@code": entry.reaction[0].manifestation[0].coding[0].code,
                "@displayName": entry.reaction[0].manifestation[0].coding[0].display,
                "@codeSystemName": "SNOMED CT",
                "@codeSystem": "2.16.840.1.113883.6.96",
            },
        },
    }

    all["act"]["entryRelationship"]["observation"] = observation

    return all
