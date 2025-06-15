# app.py - PRO MULTI-LANGUAGE VERSION
import streamlit as st
import google.generativeai as genai
import smtplib
from email.message import EmailMessage
import json

# --- Configuration ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    genai.configure(api_key=GOOGLE_API_KEY)
except (FileNotFoundError, KeyError):
    st.error("Application not configured correctly. API keys are missing in secrets.")
    st.info("If you are running the application locally, make sure you have a correctly configured .streamlit/secrets.toml file.")
    st.stop()

# Set up the model
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Helper Functions ---

# CHANGE: Using a dictionary for prompts to support multiple languages
def get_prompt_templates():
    """Returns a dictionary of prompt templates for different languages."""
    templates = {
        'Polski': """Jesteś klientem sklepu internetowego o nazwie "{store_name}". Twoim zadaniem jest dokładne przeanalizowanie poniższych regulaminów. Na ich podstawie, wygeneruj {num_emails} różnych, realistycznych zapytań e-mail od klientów. BARDZO WAŻNE: W swoich pytaniach, jeśli to stosowne, odnoś się do konkretnego numeru zamówienia: "{order_number}". Zwróć odpowiedź WYŁĄCZNIE w formacie JSON. POLITYKI SKLEPU:\n---\n{policy_text}""",
        'English': """You are a customer of an online store named "{store_name}". Your task is to carefully analyze the following store policies. Based on them, generate {num_emails} different, realistic email inquiries from customers. VERY IMPORTANT: In your questions, where appropriate, refer to the specific order number: "{order_number}". Return the response EXCLUSIVELY in JSON format. STORE POLICIES:\n---\n{policy_text}""",
        'Español': """Eres un cliente de una tienda online llamada "{store_name}". Tu tarea es analizar detenidamente las siguientes políticas de la tienda. Basándote en ellas, genera {num_emails} consultas de correo electrónico diferentes y realistas. MUY IMPORTANTE: En tus preguntas, cuando sea apropiado, haz referencia al número de pedido específico: "{order_number}". Devuelve la respuesta EXCLUSIVAMENTE en formato JSON. POLÍTICAS DE LA TIENDA:\n---\n{policy_text}""",
        'Français': """Vous êtes un client d'une boutique en ligne nommée "{store_name}". Votre tâche est d'analyser attentivement les politiques suivantes du magasin. Sur cette base, générez {num_emails} demandes par e-mail différentes et réalistes. TRÈS IMPORTANT : Dans vos questions, le cas échéant, référez-vous au numéro de commande spécifique : "{order_number}". Retournez la réponse EXCLUSIVEMENT au format JSON. POLITIQUES DU MAGASIN:\n---\n{policy_text}""",
        'Deutsch': """Sie sind ein Kunde eines Online-Shops namens "{store_name}". Ihre Aufgabe ist es, die folgenden Geschäftsbedingungen sorgfältig zu analysieren. Erstellen Sie auf dieser Grundlage {num_emails} verschiedene, realistische E-Mail-Anfragen. SEHR WICHTIG: Beziehen Sie sich in Ihren Fragen gegebenenfalls auf die spezifische Bestellnummer: "{order_number}". Geben Sie die Antwort AUSSCHLIESSLICH im JSON-Format zurück. GESCHÄFTSBEDINGUNGEN:\n---\n{policy_text}""",
        'Italiano': """Sei un cliente di un negozio online chiamato "{store_name}". Il tuo compito è analizzare attentamente le seguenti politiche del negozio. Sulla base di esse, genera {num_emails} richieste e-mail diverse e realistiche. MOLTO IMPORTANTE: Nelle tue domande, se del caso, fai riferimento al numero d'ordine specifico: "{order_number}". Restituisci la risposta ESCLUSIVAMENTE in formato JSON. POLITICHE DEL NEGOZIO:\n---\n{policy_text}""",
        'Nederlands': """U bent een klant van een online winkel genaamd "{store_name}". Uw taak is om de volgende winkelbeleidsregels zorgvuldig te analyseren. Genereer op basis daarvan {num_emails} verschillende, realistische e-mailvragen. ZEER BELANGRIJK: Verwijs in uw vragen, waar van toepassing, naar het specifieke bestelnummer: "{order_number}". Retourneer het antwoord UITSLUITEND in JSON-formaat. WINKELBELEID:\n---\n{policy_text}""",
        'Čeština': """Jste zákazníkem internetového obchodu s názvem "{store_name}". Vaším úkolem je pečlivě analyzovat následující obchodní podmínky. Na jejich základě vygenerujte {num_emails} různých, realistických e-mailových dotazů. VELMI DŮLEŽITÉ: Ve svých dotazech se případně odkažte na konkrétní číslo objednávky: "{order_number}". Odpověď vraťte VÝHRADNĚ ve formátu JSON. OBCHODNÍ PODMÍNKY:\n---\n{policy_text}""",
        'Slovenčina': """Ste zákazníkom internetového obchodu s názvom "{store_name}". Vašou úlohou je dôkladne analyzovať nasledujúce obchodné podmienky. Na ich základe vygenerujte {num_emails} rôznych, realistických e-mailových dopytov. VEĽMI DÔLEŽITÉ: Vo svojich otázkach sa prípadne odvolajte na konkrétne číslo objednávky: "{order_number}". Odpoveď vráťte VÝHRADNE vo formáte JSON. OBCHODNÉ PODMIENKY:\n---\n{policy_text}""",
        'Română': """Sunteți clientul unui magazin online numit "{store_name}". Sarcina dvs. este să analizați cu atenție următoarele politici ale magazinului. Pe baza acestora, generați {num_emails} de cereri de e-mail diferite și realiste. FOARTE IMPORTANT: În întrebările dvs., acolo unde este cazul, faceți referire la numărul de comandă specific: "{order_number}". Returnați răspunsul EXCLUSIV în format JSON. POLITICILE MAGAZINULUI:\n---\n{policy_text}"""
    }
    return templates

def generate_test_emails(policy_text, store_name, order_number, language, num_emails=5):
    """Generates test emails based on store policy, order number, and selected language."""
    st.info(f"🤖 Thinking... Generating emails in {language} using Gemini. This may take a moment.")
    
    prompt_templates = get_prompt_templates()
    # Get the correct prompt template for the selected language, default to English if not found
    prompt_template = prompt_templates.get(language, prompt_templates['English'])
    
    # Format the prompt with the provided details
    prompt = prompt_template.format(
        store_name=store_name,
        order_number=order_number,
        num_emails=num_emails,
        policy_text=policy_text
    )

    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```")
        return cleaned_response
    except Exception as e:
        st.error(f"An error occurred while communicating with the Gemini API: {e}")
        return None

def send_email(subject, body, to_email):
    """Sends a single email using Gmail's SMTP server."""
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
        st.error(f"Failed to send email: '{subject}'. Error: {e}")
        return False

# --- Main Streamlit App ---

st.set_page_config(page_title="Test Email Generator", page_icon="📧", layout="wide")
st.title("E-commerce Test Email Generator 📧")
st.markdown("A tool for your customer service team. Upload store policies, and the AI will generate and send test emails.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Step 1: Enter Details")
    store_name = st.text_input("Store Name", "SuperStore")
    customer_service_email = st.text_input("Customer Service Email (recipient)", "contact@yourstore.com")
    order_number = st.text_input("Sample Order Number", "ORD/123/2025")
    
    # CHANGE: Added more languages to the selection box
    language = st.selectbox(
        "Language for Generated Emails",
        ('Polski', 'English', 'Español', 'Français', 'Deutsch', 'Italiano', 'Nederlands', 'Čeština', 'Slovenčina', 'Română')
    )

with col2:
    st.subheader("Step 2: Upload Policies")
    uploaded_files = st.file_uploader(
        "Choose .txt files with your store policies",
        type=['txt'],
        accept_multiple_files=True
    )

st.divider()

if uploaded_files:
    st.subheader("Step 3: Generate & Send Emails")
    
    if st.button("🚀 Generate and Send Test Emails", type="primary"):
        if not all([store_name, customer_service_email, order_number]):
            st.warning("Please fill in all fields in Step 1.")
        else:
            all_policies = ""
            for uploaded_file in uploaded_files:
                try:
                    all_policies += uploaded_file.read().decode("utf-8") + "\n\n---\n\n"
                except Exception as e:
                    st.error(f"Failed to read file {uploaded_file.name}: {e}")
            
            generated_json_str = generate_test_emails(all_policies, store_name, order_number, language)
            
            if generated_json_str:
                try:
                    emails_to_send = json.loads(generated_json_str)
                    st.success(f"✅ Gemini generated {len(emails_to_send)} emails. Starting dispatch...")
                    
                    progress_bar = st.progress(0, text="Sending...")
                    for i, email_data in enumerate(emails_to_send):
                        subject = email_data.get("subject", "No subject")
                        body = email_data.get("body", "No content")
                        
                        if send_email(subject, body, customer_service_email):
                            st.write(f"✔️ Sent: *{subject}*")
                        else:
                            st.write(f"❌ Sending error.")
                        
                        progress_bar.progress((i + 1) / len(emails_to_send), text=f"Sending email {i+1}/{len(emails_to_send)}")

                    st.balloons()
                    st.success("🎉 All emails have been sent!")
                    
                except json.JSONDecodeError:
                    st.error("Critical Error: The response from the AI is not in a valid JSON format.")
                    st.code(generated_json_str, language="text")
else:
    st.info("Upload policy files in Step 2 to continue.")