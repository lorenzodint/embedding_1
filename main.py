import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os


# ESECUZIONE:
# aprire il terminale ( ctrl + ò ) e digitare il comando: streamlit run main.py


# ESEMPI DOMANDE:
# - Cose'è la legge dell'inverso dell'assistenza?
# - Chi si è occupato della realizzazione grafica del documento?
# - Di cosa parla il documento fornito?
# - Quali schemi di priorità sono utilizzati in Svezia?

api = st.secrets['MOR']
client = OpenAI(api_key=api)

ASST_MOR = "asst_Gl7zDtMgHD6TSLAPdzkWN1Ca"
VS_MOR = "vs_67c6deb44c888191b2be949cdd2881e0"


def elimina_tutti_file():
    files = client.files.list()
    for f in files:
        client.files.delete(file_id=f.id)

    print(f"\nEliminazione completa dei file.\n")


def elimina_tutti_vector():
    vectors = client.beta.vector_stores.list()
    for v in vectors:
        client.beta.vector_stores.delete(vector_store_id=v.id)
    print(f"\nEliminazione completa dei vector store.\n")


def elimina_tutti_assistant():
    assistants = client.beta.assistants.list()
    for a in assistants:
        client.beta.assistants.delete(assistant_id=a.id)
    print(f"\nEliminazione completa degli assistenti.\n")


def elimina_file(file_id):
    client.files.delete(file_id=file_id)


def crea_assistente(nome):
    assistente = client.beta.assistants.create(
        name=nome,
        model="gpt-4o",
        temperature=0.6,
    )
    return assistente


def crea_vector_store(nome):
    vector_store = client.beta.vector_stores.create(name=nome)
    return vector_store


def prepara_file_e_caricamento(id_vector_store, lista_file):

    file_streams = [open(path, "rb") for path in lista_file]
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=id_vector_store,
        files=file_streams,
    )


def ottieni_lista_assistenti():
    assistenti = []

    for a in client.beta.assistants.list():
        assistenti.append(a)
    return assistenti


def ottieni_lista_vectorstore():
    vector = []
    for v in client.beta.vector_stores.list():
        vector.append(v)
    return vector


def ottieni_lista_file():
    files = []
    for f in client.files.list():
        files.append(f)
    return files


def invia_messaggio(user_input):
    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input,
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=ASST_MOR,
        # instructions="Utilizza esclusivamente i file forniti per generare una risposta.\nSe non trovi informazioni nei file forniti ignora la domanda.\nSe non trovi informazioni rilevanti nei documenti, ignora al domanda e rispondi che la richiesta non può essere soddisfatta."
        instructions=(
            "UTILIZZA ESCLUSIVAMENTE i documenti forniti.\n\n"
            "Motiva sempre la risposta citando le informazioni dei documenti che hai utilizzato.\n\n"
            "Se trovi informazioni rilevanti nei documenti forniti, argomenta ed arricchisci il più possibile di dettagli.\n\n"
            "Se non trovi informazioni RILEVANTI per soddisfare la richiesta dell'utente rispondi dicendo che non è stata trovata nessuna informazione rilevante nei documenti forniti."
            ),
    )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        # print(messages)

        risposta = messages.data[0].content[0].text.value

        print("\n\n" + "_"*100 + "\n\n")
        print(risposta)

        return risposta
    else:
        print(run.status)


def session_config():
    session = st.session_state

    session.setdefault("pagina", "chat")
    session.setdefault("error", False)
    session.setdefault("error_value", "")


def mostra_sidebar():
    session = st.session_state
    menu_laterale = st.sidebar
    with menu_laterale:
        st.title("Menu")
        st.html("<br>")
        # st.html("<br>")

        if st.button("Chat"):
            session.pagina = "chat"
            st.rerun()

        # st.html("<br>")

        if st.button("Gestisci file"):
            session.pagina = "gestisci_file"
            st.rerun()

        # st.html("<br>")

        if st.button("Aggiungi file"):
            session.pagina = "aggiungi_file"
            st.rerun()
            
        st.html("<br>")
        
        st.header("Domande di esempio:")
        st.caption("- Cos'e la legge dell'inverso dell'assistenza?")
        st.caption("- Chi si è occupato della realizzazione grafica del documento che ti è stato fornito?")
        st.caption("- Di cosa parla il documento fornito?")
        st.caption("- Quali schemi di priorità sono utilizzati in Svezia?")


def mostra_aggiungi_file():
    st.title("Aggiungi File")
    st.html("<br>")
    carica_file = st.file_uploader(
        label="Carica documenti da inserire nel VectorStore",
        accept_multiple_files=True,
        type=['.txt', '.pdf'],
    )

    if carica_file:
        salva = st.button(
            label="Salva sul VectorStore"
        )

        if salva:
            lista_file = []
            with st.spinner('Preparo i file e li carico nel VectorStore...', show_time=True):
                for file in carica_file:
                    file_path = os.path.join("file", file.name)

                    with open(file_path, "wb") as f:
                        f.write(file.getvalue())

                    file = f"./file/{file.name}"
                    lista_file.append(file)

                prepara_file_e_caricamento(
                    id_vector_store=VS_MOR,
                    lista_file=lista_file,
                )
            st.success(
                "File preparati e caricati correttamente nel VectorStore")


def mostra_gestisci_file():
    st.title("Gestisci File")
    st.html("<br>")

    files = ottieni_lista_file()

    with st.container(border=True):
        for f in files:
            c1, c2 = st.columns([3, 1], vertical_alignment="center")

            st.divider()

            with c1:

                st.write(f.filename)

            with c2:
                if st.button(":x:", key=f.id):
                    elimina_file(f.id)
                    st.rerun()


def mostra_chat():
    st.title("Chat")
    st.html("<br>")

    user_input = st.chat_input(
        placeholder="Scrivi la tua domanda...",
    )

    if user_input:
        with st.chat_message(name="user"):
            st.write(user_input)
        with st.spinner("Invio richiesta all'Assistente AI...", show_time=True):
            risposta = invia_messaggio(user_input=user_input)
        with st.chat_message(name="assistant"):
            st.write(risposta)


def main():


    st.markdown(
        r"""
        <style>
        .stDeployButton {
                visibility: hidden;
            }
        </style>
        """, unsafe_allow_html=True
    )

    assistente = client.beta.assistants.retrieve(assistant_id=ASST_MOR)
    session_config()

    session = st.session_state

    if not os.path.exists("file"):
        os.makedirs("file")

    mostra_sidebar()

    if session.pagina == "chat":
        mostra_chat()
    if session.pagina == "aggiungi_file":
        mostra_aggiungi_file()
    if session.pagina == "gestisci_file":
        mostra_gestisci_file()

    # st.write(session)



if __name__ == "__main__":
    main()
