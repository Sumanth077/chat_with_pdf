import reflex as rx
import tempfile
from embedchain import App

message_style = dict(display="inline-block", padding="2em", border_radius="8px",
                     max_width=["120em", "120em", "80em", "80em", "80em", "80em"])
class State(rx.State):
    """The app state."""
    messages: list[dict] = []
    db_path: str = tempfile.mkdtemp()
    pdf_filename: str = ""
    knowledge_base_files: list[str] = []
    user_question: str = ""
    upload_status: str = ""

    def get_app(self):
        return App.from_config(
            config={
                "llm": {"provider": "ollama",
                        "config": {"model": "llama3.3", "max_tokens": 250, "temperature": 0.5, "stream": True,
                                   "base_url": 'http://localhost:11434'}},
                "vectordb": {"provider": "chroma", "config": {"dir": self.db_path}},
                "embedder": {"provider": "ollama",
                             "config": {"model": "llama3.3", "base_url": 'http://localhost:11434'}},
            }
        )

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle the file upload and processing."""
        if not files:
            self.upload_status = "No file uploaded!"
            return

        file = files[0]
        upload_data = await file.read()
        outfile = rx.get_upload_dir() / file.filename
        self.pdf_filename = file.filename

        # Save the file
        with outfile.open("wb") as file_object:
            file_object.write(upload_data)

        # Process and add to knowledge base
        app = self.get_app()
        app.add(str(outfile), data_type="pdf_file")
        self.knowledge_base_files.append(self.pdf_filename)

        self.upload_status = f"Processed and added {self.pdf_filename} to knowledge base!"

    def chat(self):
        if not self.user_question:
            return
        app = self.get_app()
        self.messages.append({"role": "user", "content": self.user_question})
        response = app.chat(self.user_question)
        self.messages.append({"role": "assistant", "content": response})
        self.user_question = ""  # Clear the question after sending

    def clear_chat(self):
        self.messages = []


color = "rgb(107,99,246)"


def index():
    return rx.vstack(
        rx.heading("Chat with PDF using Llama 3.2"),
        rx.text("This app allows you to chat with a PDF using Llama 3.2 running locally with Ollama!"),
        rx.hstack(
            rx.vstack(
                rx.heading("PDF Upload"),
                rx.upload(
                    rx.vstack(
                        rx.button(
                            "Select PDF File",
                            color=color,
                            bg="white",
                            border=f"1px solid {color}",
                        ),
                        rx.text("Drag and drop PDF file here or click to select"),
                    ),
                    id="pdf_upload",
                    multiple=False,
                    accept={".pdf": "application/pdf"},
                    max_files=1,
                    border=f"1px dotted {color}",
                    padding="2em",
                ),
                rx.hstack(rx.foreach(rx.selected_files("pdf_upload"), rx.text)),
                rx.button(
                    "Upload and Process",
                    on_click=State.handle_upload(rx.upload_files(upload_id="pdf_upload")),
                ),
                rx.button(
                    "Clear",
                    on_click=rx.clear_selected_files("pdf_upload"),
                ),
                rx.text(State.upload_status),  # Display upload status
                width="50%",
            ),
            rx.vstack(
                rx.foreach(
                    State.messages,
                    lambda message, index: rx.cond(
                        message["role"] == "user",
                        rx.box(
                            rx.text(message["content"]),
                            background_color="rgb(0,0,0)",
                            padding="10px",
                            border_radius="10px",
                            margin_y="5px",
                            width="100%",
                        ),
                        rx.box(
                            rx.text(message["content"]),
                            background_color="rgb(0,0,0)",
                            padding="10px",
                            border_radius="10px",
                            margin_y="5px",
                            width="100%",
                        ),
                    )
                ),
                rx.hstack(
                    rx.input(
                        placeholder="Ask a question about the PDF",
                        id="user_question",
                        value=State.user_question,
                        on_change=State.set_user_question,
                        **message_style,
                    ),
                    rx.button("Send", on_click=State.chat),
                ),
                rx.button("Clear Chat History", on_click=State.clear_chat),
                width="50%",
                height="100vh",
                overflow="auto",
            ),
            width="100%",
        ),
        padding="2em",
    )


app = rx.App()
app.add_page(index)
