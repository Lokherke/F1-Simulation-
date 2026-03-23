import os
from dotenv import load_dotenv

load_dotenv()  # Add this near the top

app = Flask(__name__, ...)
DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
app.run(debug=DEBUG)
