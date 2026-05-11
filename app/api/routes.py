from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.models.schemas import QueryRequest, ESGAssessmentResult, PipelineQueryRequest
from app.services.esg_service import ESGService, get_esg_service
from app.services.twse_service import CompanyNotFoundError, TWSEServiceError

router = APIRouter()


@router.post(
    "/query",
    response_model=ESGAssessmentResult,
    status_code=status.HTTP_200_OK,
    tags=["esg"],
    summary="Run an ESG query for a company",
)
async def query_esg(
    payload: QueryRequest = Body(...),
    service: ESGService = Depends(get_esg_service),
) -> ESGAssessmentResult:
    try:
        return await service.process_query(payload)
    except CompanyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TWSEServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve data from the TWSE OpenAPI.",
        ) from exc


@router.post(
    "/query/pipeline",
    status_code=status.HTTP_200_OK,
    tags=["esg"],
    summary="Run role/pillar/intent ESG pipeline",
)
async def query_esg_pipeline(
    payload: PipelineQueryRequest = Body(...),
    service: ESGService = Depends(get_esg_service),
) -> dict:
    try:
        return await service.process_pipeline_query(payload.query)
    except CompanyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TWSEServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve data from the TWSE OpenAPI.",
        ) from exc


@router.post(
    "/query/intent-pipeline",
    status_code=status.HTTP_200_OK,
    tags=["esg"],
    summary="Run intent-metric extraction pipeline",
)
async def query_esg_intent_pipeline(
    payload: PipelineQueryRequest = Body(...),
    service: ESGService = Depends(get_esg_service),
) -> dict:
    try:
        return await service.process_intent_pipeline_query(payload.query)
    except CompanyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TWSEServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve data from the TWSE OpenAPI.",
        ) from exc


@router.post("/compare")
async def compare_esg(payload: dict = Body(...), service: ESGService = Depends(get_esg_service)):
    out = []
    for c in payload.get("companies", []):
        # We create a dummy object matching QueryRequest properties to pass to process_query
        class DummyPayload:
            company = c
            role = payload.get("role", "investor")
            topic = payload.get("topic", "ESG")
            
        try:
            res = await service.process_query(DummyPayload())
            out.append(res)
        except Exception as e:
            out.append({"company": c, "error": str(e)})
            
    return {"results": out}
