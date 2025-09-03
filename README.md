#  BookStoreAIManager

BookStoreAIManager is a bookstore management system with AI chatbot support.  
It allows staff to manage books, orders, and sales while providing a customer-friendly interface with a chatbot that can answer questions about the store.

---

##  Features

- **Staff Management**
  - Add books, create orders, complete payments
  - Profit, revenue, and expense analysis
  - Order history with details

- **Customer View**
  - Real-time cart synced with staff actions
  - AI chatbot for book search and store questions
  - Multilingual support (translation built-in)

- **AI Integration**
  - OpenAI GPT for chatbot answers
  - `pyttsx3` for offline text-to-speech
  - `SpeechRecognition` for voice input
  - `deep-translator` for language translation

---

## Installation

1. **Clone the project**
   ```bash
   git clone https://github.com/yourusername/BookStoreAIManager.git
   cd BookStoreAIManager
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your OpenAI API Key**
   ```powershell
   setx OPENAI_API_KEY "your_api_key_here"
   ```

---

## Usage

Run the main application:

```bash
python src/main.py
```

- **Staff Tab**:  
  - Add books to order  
  - Remove items from order  
  - Complete payment → order is saved to database  

- **Customer Tab**:  
  - See current order in real time  
  - Ask chatbot about books (title, author, description, shelf location)  
  - Get AI answers in English or Vietnamese  

- **History Tab**:  
  - Search, view, and export order history  
  - Check total amount and profit over time  

---

## Voice & Translation

- **Voice Input**: Customers can use microphone to ask questions.  
- **Text-to-Speech**: AI chatbot can read out answers (using `pyttsx3`).  
- **Translation**: All chatbot responses can be translated (via `deep-translator`).  

---

##  Requirements

- Python 3.10+  
- Dependencies in `requirements.txt`:  
  - `openai`, `pandas`, `numpy`, `tkcalendar`, `pyttsx3`,  
  - `SpeechRecognition`, `PyAudio`, `deep-translator`, `openpyxl`  
  - `matplotlib` (for charts)  

---

##  Notes

- No internet is required for text-to-speech (`pyttsx3`).  
- Internet is required for:
  - OpenAI GPT responses  
  - Google Translator API (`deep-translator`)  

---

## License

This project is for educational purposes.  
Developed as a bookstore AI management demo.
