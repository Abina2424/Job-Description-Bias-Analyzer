# Quick Start Guide

## Prerequisites Check

- ✅ Python 3.9+ installed
- ✅ Node.js 18+ installed
- ✅ Supabase account created
- ✅ OpenAI API key obtained

## 5-Minute Setup

### 1. Backend Setup (2 minutes)

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` file:
```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
WEBHOOK_URL=https://your-webhook.com  # Optional
```

Run SQL schema:
- Go to Supabase Dashboard → SQL Editor
- Copy contents of `supabase_schema.sql`
- Execute

Start server:
```bash
uvicorn app.main:app --reload
```

### 2. Frontend Setup (2 minutes)

```bash
cd frontend
npm install
npm run dev
```

### 3. Test (1 minute)

1. Open http://localhost:5173
2. Paste a job description like:
   "We're looking for an aggressive, competitive rockstar developer who can dominate the market."
3. See the bias analysis!

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (need 3.9+)
- Verify all dependencies installed: `pip list`
- Check .env file exists and has valid keys

**Frontend won't connect:**
- Verify backend is running on port 8000
- Check browser console for CORS errors
- Verify `VITE_API_URL` in frontend/.env (or defaults to localhost:8000)

**Supabase errors:**
- Verify table was created: Check Supabase Dashboard → Table Editor
- Check SUPABASE_URL and SUPABASE_KEY in .env
- Ensure service role key (not anon key) is used

**LangGraph errors:**
- Update langgraph: `pip install --upgrade langgraph langchain`
- Check OpenAI API key is valid

## Next Steps

- Customize bias keyword lists in `backend/app/graph.py`
- Adjust UI styling in `frontend/src/index.css`
- Configure webhook URL for production
- Add authentication if needed
