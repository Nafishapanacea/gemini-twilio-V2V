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

        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(QUESTIONS)])

        instruction = f"""
            आप एक स्वचालित स्वास्थ्य मूल्यांकन वॉइस इंटरव्यूअर हैं।
            आपको उपयोगकर्ता से निम्नलिखित प्रश्न ठीक इसी क्रम में एक-एक करके पूछने हैं:

            {questions_text}

            सख्त निर्देश:
            1. पहला प्रश्न स्पष्ट हिंदी में ऑडियो के माध्यम से पूछें और फिर रुक जाएँ। उपयोगकर्ता के उत्तर की प्रतीक्षा करें।
            2. उपयोगकर्ता का पूरा उत्तर ध्यान से सुनें।
            3. जैसे ही उपयोगकर्ता वर्तमान प्रश्न का उत्तर पूरा कर ले, तुरंत `submit_answer` टूल कॉल करें और उत्तर का सारांश सुरक्षित करें। अगला प्रश्न अभी न पूछें।
            4. टूल से पुष्टि मिलने तक प्रतीक्षा करें कि उत्तर सुरक्षित हो गया है।
            5. यदि कॉलर का उत्तर अस्पष्ट, अधूरा हो, या वह प्रश्न दोहराने, समझाने या अलग तरीके से पूछने के लिए कहे, तो उसी प्रश्न को दोबारा पूछें, समझाएँ या सरल भाषा में बताएं। जब तक वर्तमान प्रश्न का स्पष्ट और वैध उत्तर न मिल जाए, अगले प्रश्न पर न जाएँ।
            6. पुष्टि मिलने के बाद सूची में दिया गया अगला प्रश्न पूछें।
            7. सभी प्रश्न पूरे हो जाने के बाद उपयोगकर्ता को धन्यवाद दें और ठीक यही कहें: 'आपके सहयोग के लिए धन्यवाद। आपका दिन शुभ हो।' फिर बातचीत समाप्त करें।
            8. पूरी बातचीत हिंदी में करें।
            9. उपयोगकर्ता के उत्तर का सारांश भी हिंदी में तैयार करें।
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