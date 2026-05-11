
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Core Data Structures ---

class QueryRequest(BaseModel):
    """Schema for incoming user queries."""
    user_id: str
    company: str
    role: str
    topic: str


class PipelineQueryRequest(BaseModel):
    """Schema for the role/pillar/intent pipeline entrypoint."""
    query: str


class SourceDocumentChunk(BaseModel):
    """Represents a chunk of text retrieved from a PDF document."""
    source: str = Field(..., description="The original file source (e.g., 'AnnualReport2023.pdf').")
    text_chunk: str = Field(..., description="The extracted and processed text content chunk.")
    metadata: dict = Field({}, description="Metadata associated with the chunk, such as page number or section name.")


class ESGScore(BaseModel):
    """Structured score for a single ESG pillar (E, S, or G)."""
    pillar: str = Field(..., description="The specific ESG pillar ('Environmental', 'Social', or 'Governance').")
    score: float = Field(..., ge=0.0, le=10.0, description="A quantifiable score out of 10.")
    justification: str = Field(..., description="Detailed justification for the given score based on provided context.")


class ESGAssessmentResult(BaseModel):
    """Comprehensive result structure containing multiple scores and overall summary."""
    company_name: str = Field(..., description="The name of the company being assessed.")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="A calculated composite score based on all pillars.")
    esg_scores: List[ESGScore] = Field(..., description="List of structured scores for E, S, and G pillars.")
    summary: str = Field(..., description="A narrative summary of the company's overall ESG performance.")


class ComparisonResult(BaseModel):
    """Schema used when comparing two companies."""
    company_a: ESGAssessmentResult = Field(..., description="The assessment result for Company A.")
    company_b: ESGAssessmentResult = Field(..., description="The assessment result for Company B.")
    comparison_narrative: str = Field(..., description="A textual comparison highlighting the strengths and weaknesses of both companies based on their scores and provided context.")


# --- RAG Context & Ingestion Models ---

class SearchQuery(BaseModel):
    """Input model for vector search queries."""
    query: str = Field(..., description="The natural language query to perform the search.")
    k: int = Field(5, description="Number of top chunks (k) to retrieve from the vector database.")


# --- Persona-based output schema (Optional future use) ---

class PersonaOutputRequest(BaseModel):
    """Defines the parameters for generating persona-specific content."""
    persona: str = Field("general", enum=["investor", "job_seeker", "academic"], description="The perspective of the intended reader.")
    focus_area: Optional[str] = Field(None, description="Specific area of interest (e.g., 'carbon footprint', 'work-life balance').")