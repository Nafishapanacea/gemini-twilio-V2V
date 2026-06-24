from google import genai
from google.genai import types

from app.interview import QUESTIONS


class GeminiInterview:

    def __init__(self, api_key):

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = "gemini-3.1-flash-live-preview"

    def get_tools(self):

        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="submit_answer",
                        description="Save answer",
                        parameters={
                            "type": "OBJECT",
                            "properties": {
                                "answer": {
                                    "type": "STRING"
                                }
                            },
                            "required": ["answer"]
                        }
                    )
                ]
            )
        ]

    def build_config(self):

        instruction = """
You are conducting a structured medical interview with the user.
There are exactly 8 predefined questions you must ask.
Here are the rules you must strictly follow:
1. You must ask one question at a time. Do not ask multiple questions at once.
2. The current question you need to ask is provided to you in the text channel (from the role 'user', representing the system) in the form of 'Ask: <question_text>' or 'Ask exactly: <question_text>'. You must treat this as your directive of the current question to ask.
3. The caller's voice responses will arrive via the audio channel. Analyze their audio responses.
4. If the caller's response is unclear, incomplete, or if the caller asks you to repeat, rephrase, or explain the question, you should repeat, rephrase, or clarify that specific question. Do not move on to the next question until you have got a valid, clear response from the caller for the current question.
5. Once the caller provides a clear response to the current question, you MUST extract the answer and call the tool `submit_answer(answer=...)` with the text of their answered response.
6. When calling `submit_answer`, do not output speech telling the user what the next question is, as the system will provide the next question to you after the tool execution. You can just say a simple acknowledgment like 'Okay', 'Got it', or 'Thank you', then call the tool.
7. Only after calling `submit_answer` and receiving the tool response, the system will send you the next question instruction in the text channel. You will then ask that next question.
8. Speak in a friendly, professional, and empathetic tone. Keep your speech concise and clear as this is a voice call.
"""

        return types.LiveConnectConfig(
            response_modalities=[
                types.Modality.AUDIO
            ],
            system_instruction=types.Content(
                parts=[
                    types.Part(
                        text=instruction
                    )
                ]
            ),
            tools=self.get_tools()
        )