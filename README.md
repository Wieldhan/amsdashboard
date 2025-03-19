# AMS Dashboard

A Streamlit-based dashboard for monitoring and analyzing AMS data, with funding and lending modules.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.example` with your configuration
   - Be sure to set a secure `ADMIN_DEFAULT_PASSWORD` in your `.env` file
5. Create `.streamlit/secrets.toml` for Streamlit-specific secrets if needed

## Running the Dashboard

```
streamlit run main.py
```

## Security Considerations

- Never commit the `.env` file or `.streamlit/secrets.toml` to version control
- Sensitive API keys and database credentials should only be stored in environment variables
- For production, use a proper secrets management solution
- Database connection strings in the repository have been removed and replaced with placeholders
- **Important**: Change the default admin password immediately after first login
- Supabase API keys and service role keys should be kept secure and never exposed publicly

## Features

- Funding Dashboard: View funding metrics, deposit trends, and savings analysis
- Lending Dashboard: View lending metrics, financing trends, and NPF analysis 