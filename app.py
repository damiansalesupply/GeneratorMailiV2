# app.py - WERSJA Z FORMULARZEM NA GŁÓWNEJ STRONIE
import streamlit as st
import google.generativeai as genai
import smtplib
from email.message import EmailMessage
import json

# --- Konfiguracja ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    # Konfiguracja API Gemini tylko jeśli klucze są dostępne
    genai.configure(api_key=GOOGLE_API_KEY)
except (FileNotFoundError, KeyError):
    st.error("Aplikacja nie została poprawnie skonfigurowana. Brakuje kluczy API w sekretach.")
    st.info("Jeśli uruchamiasz aplikację lokalnie, upewnij się, że masz plik .streamlit/secrets.toml")
    st.stop()


# Ustawienie modelu Gemini
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Funkcje pomocnicze ---

def generate_test_emails(policy_text, store_name, num_emails=5):
    """Generuje e-maile testowe na podstawie polityki sklepu przy użyciu Gemini."""
    st.info("🤖 Myślę... Generuję e-maile przy użyciu Gemini. To może chwilę potrwać.")
    
    prompt = f"""
    Jesteś klientem sklepu internetowego o nazwie "{store_name}".
    Twoim zadaniem jest dokładne przeanalizowanie poniższych regulaminów i polityk tego sklepu.
    Na ich podstawie, wygeneruj {num_emails} różnych, realistycznych zapytań e-mail od klientów, które bezpośrednio odnoszą się do tych zapisów.
    Pytania powinny być zróżnicowane - od prostych, po bardziej skomplikowane lub nietypowe przypadki.

    POLITYKI SKLEPU:
    ---
    {policy_text}
    ---
    
    Zwróć odpowiedź WYŁĄCZNIE w formacie JSON, który jest listą obiektów. Każdy obiekt musi zawierać klucz "subject" (temat maila) i "body" (treść maila).
    Nie dodawaj żadnych innych komentarzy ani tekstu poza JSONem.
    """

    try:
        response = model.generate_content(prompt)
        # Usuwamy znaczniki bloku kodu z odpowiedzi, jeśli Gemini je doda
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```")
        return cleaned_response
    except Exception as e:
        st.error(f"Wystąpił błąd podczas komunikacji z API Gemini: {e}")
        return None

def send_email(subject, body, to_email):
    """Wysyła pojedynczy e-mail z użyciem serwera SMTP Gmaila."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Nie udało się wysłać maila: '{subject}'. Błąd: {e}")
        return False

# --- Główna aplikacja Streamlit ---

st.set_page_config(page_title="Generator Maili Testowych", page_icon="📧", layout="wide")
st.title("Generator Maili Testowych dla E-commerce 📧")
st.markdown("Narzędzie dla Twojego zespołu BOK. Wgraj regulaminy, a AI wygeneruje i wyśle maile testowe.")

st.divider() # Pozioma linia dla lepszej organizacji

# ### ZMIANA TUTAJ: Usunęliśmy 'with st.sidebar:' ###
# Poniższe elementy będą teraz widoczne bezpośrednio na głównej stronie.

# Użyjemy kolumn, żeby ładniej to wyglądało
col1, col2 = st.columns(2)

with col1:
    st.subheader("Krok 1: Wprowadź dane")
    store_name = st.text_input("Nazwa sklepu", "SuperSklep")
    customer_service_email = st.text_input("Adres e-mail BOK (odbiorca)", "kontakt@twojsklep.pl")

with col2:
    st.subheader("Krok 2: Wgraj regulaminy")
    uploaded_files = st.file_uploader(
        "Wybierz pliki .txt z politykami Twojego sklepu",
        type=['txt'],
        accept_multiple_files=True
    )

st.divider()

# Dalsza logika aplikacji
if uploaded_files:
    st.subheader("Krok 3: Wygeneruj i wyślij e-maile")
    
    # Przycisk na środku, żeby był dobrze widoczny
    if st.button("🚀 Generuj i Wyślij Maile Testowe", type="primary"):
        if not store_name or not customer_service_email:
            st.warning("Uzupełnij nazwę sklepu i e-mail odbiorcy w krokach 1 i 2.")
        else:
            # Wczytywanie treści plików
            all_policies = ""
            for uploaded_file in uploaded_files:
                try:
                    all_policies += uploaded_file.read().decode("utf-8") + "\n\n---\n\n"
                except Exception as e:
                    st.error(f"Nie udało się odczytać pliku {uploaded_file.name}: {e}")
            
            # Generowanie maili
            generated_json_str = generate_test_emails(all_policies, store_name)
            
            if generated_json_str:
                try:
                    emails_to_send = json.loads(generated_json_str)
                    st.success(f"✅ Gemini wygenerował {len(emails_to_send)} e-maili. Rozpoczynam wysyłkę...")
                    
                    progress_bar = st.progress(0, text="Wysyłanie...")
                    for i, email_data in enumerate(emails_to_send):
                        subject = email_data.get("subject", "Brak tematu")
                        body = email_data.get("body", "Brak treści")
                        
                        if send_email(subject, body, customer_service_email):
                            st.write(f"✔️ Wysłano: *{subject}*")
                        else:
                            st.write(f"❌ Błąd wysyłki: *{subject}*")
                        
                        progress_bar.progress((i + 1) / len(emails_to_send), text=f"Wysyłanie maila {i+1}/{len(emails_to_send)}")

                    st.balloons()
                    st.success("🎉 Wszystkie maile zostały wysłane!")
                    
                except json.JSONDecodeError:
                    st.error("Błąd krytyczny: Odpowiedź od AI nie jest w poprawnym formacie JSON.")
                    st.code(generated_json_str, language="text")
else:
    st.info("Wgraj pliki z politykami w Kroku 2, aby kontynuować.")