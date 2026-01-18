# Job Description Bias Analyzer

An AI-powered tool that analyzes job descriptions for gender bias in language, provides explanations, and suggests inclusive alternatives.

## Features

- **Bias Detection**: Automatically detects masculine-coded, feminine-coded, or neutral language
- **AI-Powered Analysis**: Uses OpenAI to generate detailed explanations and inclusive alternatives
- **LangGraph Workflow**: Structured conversation flow with routing and state management
- **Supabase Integration**: Stores all analysis results in a PostgreSQL database
- **Webhook Support**: Triggers webhook when analysis is complete
- **Chat Interface**: Clean, modern React frontend for easy interaction

## Tech Stack

- **Frontend**: React + Vite
- **Backend**: FastAPI + LangGraph
- **Database**: Supabase (PostgreSQL)
- **AI**: OpenAI GPT-3.5-turbo

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
WEBHOOK_URL=your_webhook_url_here  # Optional
```

5. Set up Supabase table:

Run this SQL in your Supabase SQL editor:

```sql
CREATE TABLE IF NOT EXISTS job_analyses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  job_description TEXT NOT NULL,
  biased_terms TEXT[],
  bias_type TEXT CHECK (bias_type IN ('masculine', 'feminine', 'neutral')),
  bias_explanation TEXT,
  inclusive_alternative TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

6. Start the backend server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file (optional, defaults to localhost:8000):
```bash
echo "VITE_API_URL=http://localhost:8000" > .env
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. Open the frontend in your browser
2. Paste or type a job description in the chat input
3. The AI will analyze the text and provide:
   - Detected biased terms
   - Explanation of why the language may be biased
   - Suggested inclusive alternatives
4. Results are automatically stored in Supabase and sent to the webhook (if configured)

## API Endpoints

### POST /chat

Send a job description for analysis.

**Request:**
```json
{
  "message": "We are looking for an aggressive, competitive rockstar developer...",
  "conversation_id": "optional-uuid"
}
```

**Response:**
```json
{
  "response": "**Masculine-Coded Bias Detected**\n\n...",
  "conversation_id": "uuid",
  "requires_clarification": false
}
```

### GET /health

Health check endpoint.

## Webhook Payload

When analysis is complete, the following payload is sent to the configured webhook URL:

```json
{
  "job_description": "Full job description text",
  "biased_terms": ["aggressive", "competitive", "rockstar"],
  "bias_type": "masculine",
  "bias_explanation": "Explanation of bias...",
  "inclusive_alternative": "Suggested alternative phrasing..."
}
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── graph.py         # LangGraph workflow
│   │   ├── models.py        # Pydantic models
│   │   ├── supabase_client.py
│   │   └── webhook.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── api.js
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Notes

- The system asks for clarification if the job description is incomplete
- Analysis results are stored in Supabase for future reference
- Webhook is triggered only when all required fields are collected
- The LangGraph workflow handles routing based on detected bias type
