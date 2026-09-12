from jsonschema import validate
SCHEMA = {
 "$schema":"https://json-schema.org/draft/2020-12/schema",
 "type":"object",
 "required":["answer","route","sources","escalation_score","guardrail"],
 "properties":{
   "answer":{"type":"string"},
   "route":{"enum":["rag","order_status","blocked"]},
   "sources":{"type":"array","items":{"type":"string"}},
   "escalation_score":{"type":["number","null"],"minimum":0,"maximum":1},
   "guardrail":{"type":"string"}
 }
}
def validate_response(obj):
    validate(obj, SCHEMA)
    return obj
