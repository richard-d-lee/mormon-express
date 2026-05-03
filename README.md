# Mormon Express - Scripture Conversations

An educational AI-powered chatbot that allows users to have conversations with characters from the Bible and Book of Mormon. Each character has a unique personality, speaking style, and theological perspective based on LDS-approved sources.

## Features

- **30+ Unique Characters** from three sections:
  - Book of Mormon (Nephi, Alma, Captain Moroni, Mormon, Moroni, Abinadi, King Benjamin, Enos, Ammon, Samuel the Lamanite)
  - Old Testament (Moses, Abraham, Joseph, Elijah, Ruth, David, Isaiah, Daniel, Eve, Job, Noah)
  - New Testament (Peter, Paul, Mary, John the Beloved, Martha, John the Baptist, Thomas, Luke, Mary Magdalene, Stephen)

- **User Authentication** - Save conversations across sessions
- **Daily Recommendations** - Personalized suggestions based on conversation history
- **Scripture Mode** - Include relevant scripture references in responses
- **Conversation History** - View and continue past conversations
- **Mobile Responsive** - Works on all devices

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (dev) / PostgreSQL (production)
- **AI**: Anthropic Claude API
- **Frontend**: Vanilla HTML/CSS/JavaScript

## Setup

### Prerequisites

- Python 3.9+
- Anthropic API key

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/mormon-express.git
cd mormon-express
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```

5. Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=your_api_key_here
```

6. Run the application:
```bash
python src/main.py
```

7. Open http://localhost:5000 in your browser

## Deployment to Render

### Step 1: Push to GitHub

1. Create a new repository on GitHub

2. Initialize git and push:
```bash
cd mormon-express
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mormon-express.git
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up/login

2. Click "New +" and select "Blueprint"

3. Connect your GitHub account and select the repository

4. Render will automatically detect the `render.yaml` configuration

5. Add your environment variable:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key

6. Click "Apply" to deploy

Your app will be available at `https://mormon-express.onrender.com` (or your custom domain)

### Alternative: Manual Render Setup

If you prefer manual setup:

1. Create a new "Web Service" on Render
2. Connect your repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python src/main.py`
4. Add environment variables:
   - `ANTHROPIC_API_KEY`
   - `SECRET_KEY` (generate a random string)
   - `FLASK_ENV=production`
5. Optionally create a PostgreSQL database and link it

## Character Details

Each character is crafted with:
- Unique personality traits based on scriptural accounts
- Authentic speaking patterns from their era
- Theological perspectives consistent with LDS doctrine
- References to key scriptures from their stories
- Topics they're particularly suited to discuss

## Scripture Sources

The application references:
- Book of Mormon
- Bible (Old and New Testament)
- Doctrine and Covenants
- Pearl of Great Price

## Support

If you find this project helpful, consider supporting development:
[Donate on GoFundMe](https://www.gofundme.com/f/support-buzly-privacyfirst-community-platform)

## License

MIT License - feel free to use and modify for educational purposes.
