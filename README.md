# ESG AI Agent Backend

Production-ready FastAPI backend scaffold for an ESG agent workflow.

## Features

- FastAPI app with `/query` and `/health` endpoints
- Modular service, agent, API, model, and DB layers
- MongoDB connection lifecycle using Motor
- TWSE OpenAPI integration for governance, risk, and safety datasets
- Structured ESG normalization for downstream integration
- Mock vector retrieval for supplemental context

## Project Structure

```text
app/
  api/
  agents/
  db/
  models/
  services/
  main.py
```

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Example Request

```bash
curl -X POST http://127.0.0.1:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"test\",\"company\":\"2330\",\"role\":\"investor\",\"topic\":\"governance\"}"
```

## Example Response

```json
{
  "summary": "2330 (2330) TWSE ESG data for the latest period is normalized into governance, risk, and safety sections.",
  "metrics": {
    "company": {
      "code": "2330",
      "name": "2330"
    },
    "reporting_year": null,
    "published_date": null,
    "governance": {
      "board_seats": null,
      "independent_director_seats": null,
      "female_director_seats": null,
      "female_director_ratio": null,
      "board_attendance_rate": null,
      "director_training_compliance_rate": null
    },
    "risk": {
      "major_incident_policy": null,
      "critical_material_risk_description": null
    },
    "safety": {
      "occupational_injury_count": null,
      "occupational_injury_rate": null,
      "fire_incident_count": null,
      "fire_casualty_count": null,
      "fire_casualty_rate": null
    },
    "sources": [
      {
        "dataset": "TWSE ESG board governance data",
        "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap46_L_6"
      },
      {
        "dataset": "TWSE ESG risk management policy data",
        "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap46_L_19"
      },
      {
        "dataset": "TWSE ESG occupational safety data",
        "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap46_L_21"
      }
    ]
  },
  "risk": "TWSE risk policy disclosures are unavailable for the requested company.",
  "highlights": [
    "Governance board attendance rate was not disclosed in the matched TWSE record.",
    "Director training compliance rate was not disclosed in the matched TWSE record.",
    "Occupational injury rate was not disclosed in the matched TWSE record."
  ]
}
```
