import os
import chainlit as cl
import asyncio

from typing import List, Dict
from pathlib import Path

from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Aktualisierte Importe
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.document_loaders import PyMuPDFLoader

from langchain.vectorstores.chroma import Chroma

from langchain.indexes import SQLRecordManager, index
from langchain.schema import Document
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableConfig

from openai import AsyncClient


openai_client = AsyncClient(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization='',
    )
print("Client initialisiert!" + openai_client.organization)

model_name = "gpt-4-1106-preview"
settings = {
    "temperature": 0.3,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}

embeddings_model = OpenAIEmbeddings()



def process_pdfs(pdf_storage_path, chunk_size, chunk_overlap, embeddings_model: OpenAIEmbeddings):
    pdf_directory = Path(pdf_storage_path)
    if not pdf_directory.exists():
        print(f"Das Verzeichnis {pdf_directory.absolute()} existiert nicht.")
        return None

    pdf_files = list(pdf_directory.glob("*.pdf"))
    if not pdf_files:
        print(f"Keine PDF-Dateien gefunden im Verzeichnis: {pdf_directory.absolute()}")
        return None

    docs = []  # type: List[Document]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for pdf_path in pdf_files:
        print(f"Lade PDF: {pdf_path}")
        loader = PyMuPDFLoader(str(pdf_path))
        documents = loader.load()
        if documents:
            split_docs = text_splitter.split_documents(documents)
            if split_docs:
                docs += split_docs
            else:
                print(f"Splitting von Dokumenten fehlgeschlagen für: {pdf_path}")
        else:
            print(f"Keine Dokumente in {pdf_path} gefunden oder Problem beim Laden.")

    if not docs:
        print("Keine Dokumente verfügbar zum Erstellen der Embeddings.")
        return None

    try:
        doc_search = Chroma.from_documents(docs, embeddings_model)
    except Exception as e:
        print(f"Fehler bei Chroma.from_documents: {e}")
        return None

    try:
        namespace = "chromadb/my_documents"
        record_manager = SQLRecordManager(
            namespace, db_url="sqlite:///record_manager_cache.sql"
        )
        record_manager.create_schema()

        index_result = index(
            docs,
            record_manager,
            doc_search,
            cleanup="incremental",
            source_id_key="source",
        )
        print(index_result)
    except Exception as e:
        print(f"Ein Fehler ist beim Initialisieren des RecordManagers oder beim Indexieren aufgetreten: {e}")

    return doc_search


@cl.on_chat_start
async def start_chat():
    doc_search = process_pdfs("./STORE", 2048, 100, embeddings_model)
    if doc_search is not None:
        cl.user_session.set("doc_search", doc_search)
    print("Doc Search initialisiert!")

    if doc_search is None:
        print("Die Initialisierung von doc_search ist fehlgeschlagen.")
        return

    cl.user_session.set("doc_search", doc_search)
    
    cl.user_session.set(
        "message_history",
        [
            {
                "role": "system",
                "content": "Dein Name ist Onki und du bist humorvoll und machst gelegentliche witze, als Onboarding-Assistent und technisches Genie bei MetallicaTech GmbH, ist es deine Aufgabe, neue Teammitglieder durch ihren Einstieg zu führen. Basierend auf dem folgenden Kontext:{context} Frage: {question}. Antworte präzise und vermeide lange Texte",
            }
        ],
    )
    await cl.Avatar(
        name="Onki",
        url="https://static.wikia.nocookie.net/silicon-valley/images/e/e3/Dinesh_Chugtai.jpg",
    ).send()
    

    # Abrufen der message_history aus der user_session
    message_history = cl.user_session.get("message_history")

    # Überprüfen, ob message_history existiert und mindestens einen Eintrag hat
    if message_history and len(message_history) > 0:
        # Zugriff auf den Inhalt des ersten Eintrags in message_history
        content = message_history[0]["content"]

        # Jetzt kannst du template für weitere Operationen verwenden
        print(content)


    template = content

    model = ChatOpenAI(model_name="gpt-4-1106-preview", streaming=True)
    #print("OpenAI-Modell initialisiert! ")

    prompt = ChatPromptTemplate.from_template(template)
    cl.user_session.set("prompt", prompt)

    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    retriever = doc_search.as_retriever()

    runnable = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )

    # Speichern der initialisierten Komponenten im Benutzersitzungskontext
    cl.user_session.set("model", model)
    cl.user_session.set("prompt", prompt)
    cl.user_session.set("runnable", runnable)
    cl.user_session.set("doc_search", doc_search)

    print("Initialisierung des Chat-Start-Handlers abgeschlossen.")

    # Begrüßungsnachricht und Eingabeaufforderung für den Namen.
    user_name = await prompt_for_user_name()
    if user_name:
        await greet_user_by_name(user_name)

async def prompt_for_user_name():
    try:
        response = await cl.AskUserMessage(content="Hallo, ich bin Onki, dein Onboarding-Assistent. Wie heißt du?",
                                            author="Onki",
                                            timeout=30
        ).send()
        if response and 'output' in response and response['output'].strip():
            user_name = response['output'].strip()
            cl.user_session.set("user_name", user_name)
            print(f"Name gespeichert: {user_name}")
            return user_name
    except Exception as e:
        print(f"Fehler bei der Eingabeaufforderung für den Namen: {e}")
    return None


async def greet_user_by_name(name):
    await cl.Message(content=f"Willkommen an Bord, {name}! Es ist toll, dich hier zu haben. Wenn du Fragen hast oder Hilfe beim Einstieg benötigst, zögere nicht, mich zu fragen.",
                     author="Onki",
                     ).send()


async def answer_as(name, message: cl.Message):
    # Zugriff auf die Benutzersitzung, um die gespeicherten Daten abzurufen
    message_history = cl.user_session.get("message_history")
    runnable = cl.user_session.get("runnable")

    # Erstellen der Nachrichteninstanz mit dem Autorname
    msg = cl.Message(author=name, content="")
    await msg.send()

    async for chunk in runnable.astream(
        message.content,
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.update()

    stream = await openai_client.chat.completions.create(
        model=model_name,
        messages=message_history + [{"role": "user", "content": f"speak as {name}"}],
        stream=True,
        **settings,
    )

    # Generieren der Antwort unter Berücksichtigung des Kontexts durch das Runnable
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    # Aktualisieren der Nachrichtenhistorie und Senden der Nachricht
    message_history.append({"role": "assistant", "content": msg.content})
    cl.user_session.set("message_history", message_history)
    await msg.send()




@cl.on_message
async def main(message: cl.Message):
   # Die ursprüngliche Logik für das Verarbeiten von Nachrichten
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    await asyncio.gather(
        answer_as("Onki", message)
)
