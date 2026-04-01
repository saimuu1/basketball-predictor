from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Server health status")
    version: str = Field(description="API version")


class UpcomingGame(BaseModel):
    game_id: str = Field(description="Unique game identifier")
    game_date: str = Field(description="Scheduled game date")
    team_a_id: str = Field(description="Team A identifier")
    team_b_id: str = Field(description="Team B identifier")
    team_a_name: str = Field(description="Team A display name")
    team_b_name: str = Field(description="Team B display name")
    home_team_id: str | None = Field(default=None, description="Home team ID, if applicable")
    team_a_logo: str | None = Field(default=None, description="Team A logo URL")
    team_b_logo: str | None = Field(default=None, description="Team B logo URL")


class PastGame(BaseModel):
    game_id: str = Field(description="Unique game identifier")
    game_date: str = Field(description="Game date")
    team_a_id: str = Field(description="Team A identifier")
    team_b_id: str = Field(description="Team B identifier")
    team_a_name: str = Field(description="Team A display name")
    team_b_name: str = Field(description="Team B display name")
    home_team_id: str | None = Field(default=None, description="Home team ID, if applicable")
    team_a_score: int = Field(description="Team A final score")
    team_b_score: int = Field(description="Team B final score")
    status: str = Field(description="Game status, e.g. 'Final'")
    team_a_logo: str | None = Field(default=None, description="Team A logo URL")
    team_b_logo: str | None = Field(default=None, description="Team B logo URL")


class PredictRequest(BaseModel):
    game_id: str | None = Field(default=None, description="Optional game identifier")
    game_date: str | None = Field(default=None, description="Optional game date")
    team_a_id: str = Field(description="Team A identifier")
    team_b_id: str = Field(description="Team B identifier")
    team_a_name: str = Field(description="Team A display name")
    team_b_name: str = Field(description="Team B display name")
    home_team_id: str | None = Field(default=None, description="Home team ID, if applicable")


class PredictionFactor(BaseModel):
    name: str = Field(description="Factor name, e.g. 'Recent Win Rate'")
    value: float = Field(description="Numeric value of the factor")
    impact: str = Field(description="Which team this factor favors: 'team_a', 'team_b', or 'neutral'")
    description: str = Field(description="Human-readable explanation of this factor")


class PredictResponse(BaseModel):
    predicted_winner: str = Field(description="Name of the predicted winning team")
    team_a_win_probability: float = Field(description="Team A win probability (0-1)")
    team_b_win_probability: float = Field(description="Team B win probability (0-1)")
    confidence: float = Field(description="Prediction confidence score (0-1)")
    summary: str = Field(description="Short sports-style explanation of the prediction")
    factors: list[PredictionFactor] = Field(description="Key factors driving the prediction")
    model_used: str = Field(description="'trained_model' or 'fallback'")
