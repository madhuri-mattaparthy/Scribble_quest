# Scribble Quest - AI-Powered Drawing Game

An interactive educational game that combines creative drawing with AI-powered analysis and reward generation. Kids draw simple doodles, and AI transforms them into beautiful artwork.

## Features

- **AI-Generated Challenges**: Dynamic drawing prompts created by GPT-3.5 Turbo
- **Real-time Drawing Analysis**: GPT-4 Vision analyzes drawings for accuracy
- **Personalized Rewards**: DALL-E generates custom artwork based on successful drawings
- **Interactive Canvas**: HTML5 Canvas with touch and mouse support
- **Progressive Scoring**: Points-based system with level advancement
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **OpenAI GPT-3.5 Turbo** - Challenge generation via LangChain
- **OpenAI GPT-4 Vision** - Drawing analysis and validation
- **DALL-E 3** - AI image generation for rewards
- **PIL** - Image processing and validation

### Frontend
- **HTML5 Canvas API** - Drawing interface
- **Vanilla JavaScript** - Game logic and real-time interactions
- **CSS3** - Responsive design with animations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/scribble-quest.git
cd scribble-quest
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
Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

1. Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Start drawing and let the AI analyze your artwork!

## How It Works

1. **Challenge Generation**: AI creates unique drawing prompts
2. **User Drawing**: Players draw on the interactive canvas
3. **AI Analysis**: Computer vision analyzes the drawing accuracy
4. **Reward Generation**: DALL-E creates personalized artwork for successful drawings
5. **Progression**: Players advance through levels with increasing challenges

## API Endpoints

- `GET /` - Serve the main game interface
- `GET /api/generate-questions` - Generate new drawing challenges
- `POST /api/analyze-drawing` - Analyze user drawings and generate rewards
- `GET /api/health` - Check backend health status

## Project Structure

```
scribble-quest/
├── main.py                 # FastAPI backend
├── requirements.txt        # Python dependencies
├── controllers/
│   └── vision_controller.py  # AI vision processing
├── Scribble_quest/
│   └── index.html         # Frontend game interface
└── .env                   # Environment variables (not in repo)
```

## Requirements

- Python 3.8+
- OpenAI API key with access to GPT-4 Vision and DALL-E 3
- Modern web browser with HTML5 Canvas support

## Demo

The application demonstrates practical integration of multiple AI models:
- Natural language processing for dynamic content generation
- Computer vision for real-time drawing analysis
- Generative AI for personalized visual rewards

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Contact

For questions or feedback, please open an issue on GitHub.
