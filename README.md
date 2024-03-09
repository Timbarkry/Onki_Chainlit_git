# Onboarding Assistant App

This is a simple onboarding assistant app that uses the power of Langchain and OpenAI to provide a seamless and informative onboarding experience for new employees. The app is designed to be run with the command `chainlit run app.py`, and it requires Python 3.11 to function properly.

## Features

- Loads and processes PDF documents for embedding and indexing
- Uses Langchain's Chroma vector database for efficient document search
- Integrates with OpenAI's API for conversational interactions
- Provides a custom onboarding assistant persona with specific instructions
- Supports code interpreter and document retrieval tools
- Offers a guided onboarding process with specific questions and responses based on the user's role

## Getting Started

To get started with the app, follow these steps:

1. Make sure you have Python 3.11 installed on your system.
2. Clone this repository or download the source code as a ZIP file.
3. Install the required dependencies by running `pip install -r requirements.txt`.
4. Set the `OPENAI_API_KEY` environment variable to your OpenAI API key.
5. Place the PDF documents you want to use for onboarding in the `STORE` directory.
6. Run the app with the command `chainlit run app.py`.
7. Interact with the onboarding assistant using the chat interface.

## Usage

The onboarding assistant app is designed to be interactive. When you start the app, you will be prompted to enter your name. After that, the assistant will ask you about your position in the company. Based on your response, the assistant will provide you with relevant information and resources to help you get started.

You can also ask the assistant specific questions related to your onboarding process. The assistant will use the embedded documents and the OpenAI API to provide accurate and helpful responses.

## Troubleshooting

If you encounter any issues while running the app, make sure you have the required dependencies installed and that your `OPENAI_API_KEY` environment variable is set correctly. If the problem persists, you can check the console for any error messages or logs.

## License

This app is released under the MIT License. See the `LICENSE` file for more information.
